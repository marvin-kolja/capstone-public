import asyncio
import logging
import pathlib
from contextlib import suppress
from typing import Optional
from uuid import UUID

from core.common.async_wrapper import async_wrapper
from core.device.i_device import IDevice
from core.device.i_services import IServices
from core.subprocess import ProcessException
from core.xc.commands.xcodebuild_command import IOSDestination
from core.xc.commands.xctrace_command import Instrument
from core.test_session.execution_plan import ExecutionPlan, ExecutionStep
from core.test_session.plan import XctestrunConfig
from core.test_session.session_state import (
    SessionState,
    ExecutionStepStateSnapshot,
    ExecutionStepState,
)
from core.test_session.session_step_hasher import hash_session_execution_step
from core.xc.xctest import Xctest
from core.xc.xctrace.xctrace_interface import Xctrace

logger = logging.getLogger(__name__)


class Session:
    """
    This class is responsible for running the test session.

    Attributes:
        _execution_plan (ExecutionPlan): The execution plan for the test session.
        _session_id (UUID): The unique identifier for the test session.
        _device (IDevice): The device to run the tests on.
        _output_dir (pathlib.Path): The directory to store the trace and xcresult files.
        _i_services (IServices): The services to interact with the device.
        _session_state (Optional[SessionState]): The state of the test session.
    """

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        session_id: UUID,
        device: IDevice,
        output_dir: pathlib.Path,
        queue: Optional[asyncio.Queue[ExecutionStepStateSnapshot]] = None,
    ):
        """
        :param execution_plan: The execution plan for the test session.
        :param session_id: The unique identifier for the test session.
        :param device: The device to run the tests on.
        :param output_dir: The directory to store the trace and xcresult files.
        :param queue: A queue to send the session state to.

        :raises FileNotFoundError: If the output directory does not exist.
        """
        self._execution_plan = execution_plan
        self._session_id = session_id
        self._device = device
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory '{output_dir}' does not exist.")
        self._output_dir = output_dir
        self._i_services = IServices(self._device)
        self._session_state = SessionState(
            execution_plan=self._execution_plan,
            session_id=self._session_id,
        )
        self._queue = queue

    async def run(self):
        """
        This will prepare the test session and then run the steps in the test plan.
        """
        logger.info(f"Starting test session '{self._session_id}'")
        await self._prepare()
        await self._run_execution_plan()

    async def _prepare(self):
        """
        Prepare the test session.

        This will:

        - Check if the execution plan is valid.
        - Check if the device is ready for testing.
        """
        logger.debug(f"Preparing test session '{self._session_id}'")
        if self._execution_plan.execution_steps is None:
            raise ValueError("Execution plan is not planned.")
        if not self._execution_plan.execution_steps:
            raise ValueError("No execution steps found in the plan.")
        self._device.check_dvt_ready()

    async def _run_execution_plan(self):
        """
        Uses the execution plan to execute the execution steps one by one.
        """
        number_of_steps = len(self._execution_plan.execution_steps)

        logger.debug(
            f"Run execution plan with '{number_of_steps}' steps for test session '{self._session_id}'"
        )

        for i in range(number_of_steps):
            logger.debug(f"Getting next execution step '{i}'")
            execution_step_state = self._session_state.next_execution_step()
            execution_step_state.set_running()
            self._enqueue_state(execution_step_state.snapshot())
            try:
                await self._run_execution_step(execution_step_state)
                execution_step_state.set_completed()
                self._enqueue_state(execution_step_state.snapshot())
            except asyncio.CancelledError:
                logger.info(
                    f"Execution step cancelled. Ending test session '{self._session_id}'"
                )
                execution_step_state.set_cancelled()
                self._enqueue_state(execution_step_state.snapshot())
                raise  # Re-raise to not swallow the cancellation
            except Exception as e:
                logger.warning(f"Execution step failed", exc_info=e)
                execution_step_state.set_failed(e)
                self._enqueue_state(execution_step_state.snapshot())
                if self._execution_plan.test_plan.end_on_failure:
                    logger.info("Ending test session because of failure.")
                    # If the test plan is set to end on failure, we need to end the session.
                    break

    async def _run_execution_step(self, execution_step_state: ExecutionStepState):
        """
        Run a single execution step by using the execution step state.

        1. Handle the installation of the app and the UI test app.
        2. Generate paths for trace and xcresult files.
        3. Execute tests and record metrics.

        :param execution_step_state: The execution step state to use.
        """
        await self._handle_app_installation(execution_step_state.execution_step)
        trace_path, xcresult_path = self._generate_result_paths(
            execution_step_state.execution_step
        )
        await self._execute_test_and_trace(
            execution_step_state, trace_path, xcresult_path
        )

    def _get_app_bundle_id(self, app_path: str) -> str:
        """
        Get the app bundle id using the app path.
        :param app_path: The path to the app.
        :return: The app bundle id.
        """
        return self._execution_plan.info_plists[app_path].CFBundleIdentifier

    async def _handle_app_installation(self, execution_step: ExecutionStep):
        """
        Handle the installation of the app and the UI test app.

        1. Uninstall the apps if required
        2. Install the apps if not already installed, regardless of the reinstall_app flag

        :param execution_step: The execution step to use for the installation.
        """
        app_path = execution_step.test_target.app_path
        ui_test_app_path = execution_step.test_target.ui_test_app_path
        paths_to_install = (
            [app_path, ui_test_app_path] if ui_test_app_path else [app_path]
        )

        installed_apps = await async_wrapper(self._i_services.list_installed_apps)()

        for path_to_install in paths_to_install:
            bundle_id = self._get_app_bundle_id(path_to_install)

            if bundle_id in installed_apps and execution_step.reinstall_app:
                await async_wrapper(self._i_services.uninstall_app)(bundle_id)
                await async_wrapper(self._i_services.install_app)(path_to_install)
            elif bundle_id not in installed_apps:
                await async_wrapper(self._i_services.install_app)(path_to_install)

    def _generate_result_paths(
        self, execution_step: ExecutionStep
    ) -> tuple[pathlib.Path, pathlib.Path]:
        """
        Generate the paths for the trace and xcresult files.
        :param execution_step: The execution step to use for the generation.
        :return: The paths for the trace and xcresult files as a tuple (trace_path, xcresult_path).
        """
        base_file_path = self._output_dir / hash_session_execution_step(
            self._session_id, execution_step
        )
        trace_path = base_file_path.with_suffix(".trace")
        xcresult_path = base_file_path.with_suffix(".xcresult")
        return trace_path, xcresult_path

    async def _execute_test_and_trace(
        self,
        execution_step_state: ExecutionStepState,
        trace_path: pathlib.Path,
        xcresult_path: pathlib.Path,
    ):
        """
        Execute the test cases and record the metrics.

        1. Parse metrics to instruments
        2. Get the test cases to run
        3. Get the app bundle id
        5. Execute the test cases and record the metrics.
           - The order of how those are started depends on the recording_start_strategy.
           - Either way, both run in parallel in the end.
           - The one that executes second will wait for the app pid before starting.

        :param execution_step_state: The execution step state to use.
        :param trace_path: The path to save the trace file to.
        :param xcresult_path: The path to save the xcresult file to.
        """
        execution_step = execution_step_state.execution_step

        instruments = execution_step.instruments
        xctest_ids = execution_step.xctest_ids
        app_bundle_id = self._execution_plan.info_plists[
            execution_step.test_target.app_path
        ].CFBundleIdentifier

        trace_task = None
        test_task = None
        try:

            if execution_step.recording_start_strategy == "launch":
                trace_task = self._create_trace_launch_task(
                    trace_path, instruments=instruments, app_bundle_id=app_bundle_id
                )
                await self._i_services.wait_for_app_pid(app_bundle_id)
                test_task = self._create_xctest_task(
                    xcresult_path, xctest_ids, execution_step.xctestrun_config
                )
            elif execution_step.recording_start_strategy == "attach":
                test_task = self._create_xctest_task(
                    xcresult_path, xctest_ids, execution_step.xctestrun_config
                )
                pid = await self._i_services.wait_for_app_pid(app_bundle_id)
                trace_task = self._create_trace_attach_task(
                    trace_path, instruments=instruments, pid=pid
                )
            else:
                raise ValueError(
                    f"Invalid recording start strategy: {execution_step.recording_start_strategy}"
                )

            logger.debug(f"Awaiting tasks '{trace_task}' and '{test_task}'")

            # Await both tasks but cancel the other if one fails.
            tasks = await asyncio.wait(
                [trace_task, test_task], return_when=asyncio.FIRST_COMPLETED
            )

            if test_task in tasks[0]:
                if test_task.done() and xcresult_path.exists():
                    execution_step_state.set_xcresult_path(xcresult_path)
                    self._enqueue_state(execution_step_state.snapshot())

                if test_task.exception():
                    logger.warning(
                        f"Test task failed with exception. Cancelling trace task '{trace_task}'"
                    )
                    trace_task.cancel()
                    await trace_task
                    raise test_task.exception()
            if trace_task in tasks[0]:
                if trace_task.exception():
                    logger.warning(
                        f"Trace task failed with exception. Cancelling test task '{test_task}'"
                    )
                    test_task.cancel()
                    await test_task
                    raise trace_task.exception()
        finally:
            if test_task:
                logger.debug(f"Cleaning up test task '{test_task}'")
                test_task.cancel()
                with suppress(asyncio.CancelledError, ProcessException):
                    await test_task
            if trace_task:
                logger.debug(f"Cleaning up trace task '{trace_task}'")
                trace_task.cancel()
                with suppress(asyncio.CancelledError, ProcessException):
                    await trace_task

            if trace_path.exists() and not execution_step_state.trace_path:
                execution_step_state.set_trace_path(trace_path)
                self._enqueue_state(execution_step_state.snapshot())
            if xcresult_path.exists() and not execution_step_state.xcresult_path:
                execution_step_state.set_xcresult_path(xcresult_path)
                self._enqueue_state(execution_step_state.snapshot())

    def _create_xctest_task(
        self,
        xcresult_path: pathlib.Path,
        xctest_ids: list[str],
        xctestrun_config: XctestrunConfig,
    ):
        """
        Run the xctestrun task.

        :param xcresult_path: The path to save the xcresult file.
        :param xctest_ids: The test cases to run.
        :return: A task running the tests.
        """
        logger.debug(f"Creating xctest task for '{xctest_ids}'")
        return asyncio.create_task(
            Xctest.run_test(
                xcresult_path=xcresult_path.resolve().as_posix(),
                test_configuration=xctestrun_config.test_configuration,
                xctestrun_path=xctestrun_config.path,
                only_testing=xctest_ids,
                destination=IOSDestination(id=self._device.lockdown_service.udid),
            )
        )

    def _create_trace_launch_task(
        self,
        trace_path: pathlib.Path,
        instruments: list[Instrument],
        app_bundle_id: str,
    ):
        """
        Run the trace task using the launch strategy.
        :param trace_path: The path to save the trace file
        :param instruments: The instruments to record
        :param app_bundle_id: The app bundle id to launch
        :return: A task running the trace.
        """
        logger.debug(f"Creating trace launch task for '{app_bundle_id}'")
        return asyncio.create_task(
            Xctrace.record_launch(
                trace_path=trace_path.resolve().as_posix(),
                instruments=instruments,
                app_to_launch=app_bundle_id,
                append_trace=False,
                device=self._device.lockdown_service.udid,
            )
        )

    def _create_trace_attach_task(
        self,
        trace_path: pathlib.Path,
        instruments: list[Instrument],
        pid: int,
    ):
        """
        Run the trace task using the attach strategy.
        :param trace_path: The path to save the trace file
        :param instruments: The instruments to record
        :param pid: The process id to attach to
        :return: A task running the trace.
        """
        logger.debug(f"Creating trace attach task for '{pid}'")
        return asyncio.create_task(
            Xctrace.record_attach(
                trace_path=trace_path.resolve().as_posix(),
                instruments=instruments,
                pid=pid,
                append_trace=False,
                device=self._device.lockdown_service.udid,
            )
        )

    def _enqueue_state(self, state: ExecutionStepStateSnapshot):
        """
        Enqueue the state to the queue if available.

        If the queue is full or shutdown, this will log a warning but not raise an exception. If any other exception
        occurs, it will log an error with the exception, but not raise it.

        :param state: The state to enqueue.
        """
        try:
            if self._queue is not None:
                logger.debug(f"Enqueueing state '{state}'")
                self._queue.put_nowait(state)
        except asyncio.QueueFull:
            logging.warning("Queue is full. Dropping state.")
        except asyncio.QueueShutDown:
            logging.warning("Queue is shutdown. Dropping state.")
        except Exception as e:
            logging.error(
                "Unexpected error when putting state in the queue", exc_info=e
            )

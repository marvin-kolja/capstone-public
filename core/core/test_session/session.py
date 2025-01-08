import asyncio
import logging
from contextlib import suppress
from datetime import timedelta
from typing import Optional
from uuid import UUID

from core.device.i_device import IDevice
from core.device.i_services import IServices
from core.subprocesses.process import ProcessException
from core.subprocesses.xcodebuild_command import IOSDestination
from core.subprocesses.xctrace_command import Instrument
from core.test_session.execution_plan import ExecutionPlan, ExecutionStep
from core.test_session.metrics import parse_metrics_to_instruments
from core.test_session.session_state import SessionState
from core.test_session.session_step_hasher import hash_session_execution_step
from core.test_session.xctest import Xctest
from core.test_session.xctrace import Xctrace

logging.basicConfig(level=logging.DEBUG)


class Session:
    """
    This class is responsible for running the test session.

    Attributes:
        _execution_plan (ExecutionPlan): The execution plan for the test session.
        _session_id (UUID): The unique identifier for the test session.
        _device (IDevice): The device to run the tests on.
        _output_dir (str): The directory to store the trace and xcresult files.
        _i_services (IServices): The services to interact with the device.
        _session_state (Optional[SessionState]): The state of the test session.
    """

    def __init__(
        self,
        execution_plan: ExecutionPlan,
        session_id: UUID,
        device: IDevice,
        output_dir: str,
    ):
        """
        :param execution_plan: The execution plan for the test session.
        :param session_id: The unique identifier for the test session.
        :param device: The device to run the tests on.
        """
        self._execution_plan = execution_plan
        self._session_id = session_id
        self._device = device
        self._output_dir = output_dir
        self._i_services = IServices(self._device)
        self._session_state = SessionState(
            execution_plan=self._execution_plan,
            session_id=self._session_id,
        )

    async def run(self):
        """
        This will prepare the test session and then run the steps in the test plan.
        """
        await self._prepare()
        await self._run_execution_plan()

    async def _prepare(self):
        """
        Prepare the test session.

        This will:

        - Check if the execution plan is valid.
        - Check if the device is ready for testing.
        """
        if self._execution_plan.execution_steps is None:
            raise ValueError("Execution plan is not planned.")
        if not self._execution_plan.execution_steps:
            raise ValueError("No execution steps found in the plan.")
        self._device.check_dvt_ready()

    async def _run_execution_plan(self):
        """
        Uses the execution plan to execute the execution steps one by one.
        """
        for _ in range(len(self._execution_plan.execution_steps)):
            execution_step_state = self._session_state.next_execution_step()
            execution_step_state.set_running()
            try:
                await self._run_execution_step(execution_step_state.execution_step)
                execution_step_state.set_completed()
            except Exception as e:
                execution_step_state.set_failed(e)
                if self._execution_plan.test_plan.end_on_failure:
                    # If the test plan is set to end on failure, we need to end the session.
                    break

    async def _run_execution_step(self, execution_step: ExecutionStep):
        """
        Run an execution step.

        1. Uninstall the apps if required
        2. Install the apps if not already installed, regardless of the reinstall_app flag
        3. Parse metrics to instruments
        4. Create paths for trace and xcresult files.
        5. Execute the test cases and record the metrics.
           - The order of how those are started depends on the recording_start_strategy.
           - Either way, both run in parallel in the end.

        :param execution_step: The execution step to run.
        """
        app_path = execution_step.test_target.app_path
        ui_test_app_path = execution_step.test_target.ui_test_app_path
        app_paths = [app_path, ui_test_app_path] if ui_test_app_path else [app_path]

        installed_apps = self._i_services.list_installed_apps()

        for path_to_app in app_paths:
            bundle_id = self._execution_plan.info_plists[path_to_app].CFBundleIdentifier

            if bundle_id in installed_apps and execution_step.reinstall_app:
                self._i_services.uninstall_app(bundle_id)
                self._i_services.install_app(app_path)
            elif bundle_id not in installed_apps:
                self._i_services.install_app(app_path)

        app_bundle_id = self._execution_plan.info_plists[app_path].CFBundleIdentifier

        instruments: list[Instrument] = parse_metrics_to_instruments(
            execution_step.metrics
        )

        trace_path = f"{self._output_dir}/{hash_session_execution_step(self._session_id, execution_step)}.trace"
        xcresult_path = f"{self._output_dir}/{hash_session_execution_step(self._session_id, execution_step)}.xcresult"

        test_task = None
        trace_task = None

        test_task_builder = lambda: Xctest.run_test(
            xcresult_path=xcresult_path,
            test_configuration=self._execution_plan.test_plan.xctestrun_config.test_configuration,
            xctestrun_path=self._execution_plan.test_plan.xctestrun_config.path,
            only_testing=[
                test_case.xctest_id for test_case in execution_step.test_cases
            ],
            destination=IOSDestination(id=self._device.lockdown_service.udid),
        )

        try:
            if execution_step.recording_start_strategy == "launch":
                trace_task = asyncio.create_task(
                    Xctrace.record_launch(
                        trace_path=trace_path,
                        instruments=instruments,
                        app_to_launch=app_bundle_id,
                        append_trace=False,
                        device=self._device.lockdown_service.udid,
                    )
                )
                await self._i_services.wait_for_app_pid(app_bundle_id)
                test_task = asyncio.create_task(test_task_builder())
            elif execution_step.recording_start_strategy == "attach":
                test_task = asyncio.create_task(test_task_builder())
                pid = await self._i_services.wait_for_app_pid(
                    app_bundle_id, frequency=timedelta(milliseconds=500)
                )
                trace_task = asyncio.create_task(
                    Xctrace.record_attach(
                        trace_path=trace_path,
                        instruments=instruments,
                        pid=pid,
                        append_trace=False,
                        device=self._device.lockdown_service.udid,
                    )
                )
            else:
                raise ValueError(
                    f"Invalid recording start strategy: {execution_step.recording_start_strategy}"
                )

            # Await both tasks but cancel the trace task if the test task fails or ends
            tasks = await asyncio.wait(
                [trace_task, test_task], return_when=asyncio.FIRST_COMPLETED
            )

            if test_task in tasks[0]:
                if test_task.exception():
                    trace_task.cancel()
                    await trace_task
                    raise test_task.exception()
            if trace_task in tasks[0]:
                if trace_task.exception():
                    test_task.cancel()
                    await test_task
                    raise trace_task.exception()
        except Exception as e:
            raise
        finally:
            if test_task:
                test_task.cancel()
                with suppress(asyncio.CancelledError, ProcessException):
                    await test_task
            if trace_task:
                trace_task.cancel()
                with suppress(asyncio.CancelledError, ProcessException):
                    await trace_task

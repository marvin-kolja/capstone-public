import logging
from typing import Optional
from uuid import UUID

from core.device.i_device import IDevice
from core.device.i_services import IServices
from core.test_session.execution_plan import ExecutionPlan, ExecutionStep
from core.test_session.session_state import SessionState, ExecutionStepState

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

        :param execution_step: The execution step to run.
        """
        raise NotImplementedError

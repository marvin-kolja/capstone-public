from typing import Optional, Literal
from uuid import UUID

from core.test_session.execution_plan import ExecutionStep, ExecutionPlan


class ExecutionStepState:
    """
    This contains the state of an execution step. It stores the current status and other information about the execution
    step.

    Attributes:
        _execution_step:
        _status: The current status of the execution step.
        _exception: The exception that occurred during the execution step.
    """

    def __init__(self, execution_step: ExecutionStep):
        self._execution_step = execution_step
        self._status: Literal["not_started", "running", "completed", "failed"] = (
            "not_started"
        )
        self._exception: Optional[Exception] = None

    @property
    def status(self) -> Literal["not_started", "running", "completed", "failed"]:
        return self._status

    @property
    def execution_step(self) -> ExecutionStep:
        return self._execution_step

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception

    def set_running(self):
        self._status = "running"

    def set_completed(self):
        self._status = "completed"

    def set_failed(self, exception: Exception):
        self._status = "failed"
        self._exception = exception


class SessionState:
    """
    This class keeps track of the current state of the test session. It is responsible for managing the execution steps
    and also stores the execution step state (``ExecutionStepState``).

    Attributes:
        _execution_plan (ExecutionPlan): The execution plan for the test session.
        _session_id (UUID): The unique identifier for the test session.
        _execution_step_states (dict[str, ExecutionStepState]): The execution step states.
        _current_execution_step_index (int): The current index of the execution step. It starts from -1, indicating
            that the execution has not started, yet.
    """

    def __init__(self, execution_plan: ExecutionPlan, session_id: UUID):
        """
        :param execution_plan: The execution plan.
        :param session_id: The unique identifier for the test session.
        """
        self._execution_plan = execution_plan
        self._session_id = session_id
        self._execution_step_states: dict[str, ExecutionStepState] = {}
        self._current_execution_step_index = -1

    @property
    def total_execution_steps(self) -> int:
        """
        Gets the total number of execution
        """
        return len(self._execution_plan.execution_steps)

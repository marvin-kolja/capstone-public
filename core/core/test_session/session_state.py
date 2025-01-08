from typing import Optional, Literal
from uuid import UUID

from core.test_session.execution_plan import ExecutionStep, ExecutionPlan

StatusLiteral = Literal["not_started", "running", "completed", "failed"]


class ExecutionStepState:
    """
    This contains the state of an execution step. It stores the current status and other information about the execution
    step.

    Attributes:
        __execution_step:
        __status: The current status of the execution step.
        __exception: The exception that occurred during the execution step.
    """

    def __init__(self, execution_step: ExecutionStep):
        self.__execution_step = execution_step
        self.__status: StatusLiteral = "not_started"
        self.__exception: Optional[Exception] = None

    @property
    def status(self) -> StatusLiteral:
        return self.__status

    @property
    def execution_step(self) -> ExecutionStep:
        return self.__execution_step

    @property
    def exception(self) -> Optional[Exception]:
        return self.__exception

    def set_running(self):
        """
        Set the status to running.

        :raises ValueError: If the status is completed or failed.
        """
        if self.__status in ["completed", "failed"]:
            raise ValueError("Cannot set running after completed or failed.")
        self.__status = "running"

    def set_completed(self):
        """
        Set the status to completed.

        :raises ValueError: If the status is failed.
        """
        if self.__status == "failed":
            raise ValueError("Cannot set completed after failed.")
        self.__status = "completed"

    def set_failed(self, exception: Exception):
        """
        Set the status to failed and store the exception.

        :param exception: The exception that occurred during the execution step.

        :raises ValueError: If the status is completed.
        """
        if self.__status == "completed":
            raise ValueError("Cannot set failed after completed.")
        self.__status = "failed"
        self.__exception = exception


class SessionState:
    """
    This class keeps track of the current state of the test session. It is responsible for managing the execution steps
    and also stores the execution step state (``ExecutionStepState``).

    Attributes:
        __execution_plan (ExecutionPlan): The execution plan for the test session.
        __session_id (UUID): The unique identifier for the test session.
        __execution_step_states (dict[str, ExecutionStepState]): The execution step states.
        __current_execution_step_index (int): The current index of the execution step. It starts from -1, indicating
            that the execution has not started, yet.
    """

    def __init__(self, execution_plan: ExecutionPlan, session_id: UUID):
        """
        :param execution_plan: The execution plan.
        :param session_id: The unique identifier for the test session.
        """
        self.__execution_plan = execution_plan
        self.__session_id = session_id
        self.__execution_step_states: dict[str, ExecutionStepState] = {}
        self.__current_execution_step_index = -1

    @property
    def total_execution_steps(self) -> int:
        """
        Gets the total number of execution
        """
        return len(self.__execution_plan.execution_steps)

    def next_execution_step(self) -> Optional[ExecutionStepState]:
        """
        Increment the current execution step index and return the next execution step state.

        The returned execution step state will be stored in the execution step states dictionary.

        :return: The next execution step as a state.

        :raises IndexError: If the current execution step index is greater than the total execution steps.
        """
        raise NotImplementedError

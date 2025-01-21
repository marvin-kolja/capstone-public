import pathlib
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from core.test_session.execution_plan import ExecutionStep, ExecutionPlan
from core.test_session.session_step_hasher import hash_session_execution_step

StatusLiteral = Literal["not_started", "running", "completed", "failed", "cancelled"]


class ExecutionStepStateSnapshot(BaseModel):
    """
    Contains the current state of an execution step as a frozen data class. This can be used to represent the state of
    an execution step at a particular point in time without exposing the internal state of the execution step, which
    could be modified.

    Attributes:
        execution_step: The execution step.
        status: The current status of the execution step.
        exception: The exception that occurred during the execution step.
    """

    execution_step: ExecutionStep
    # TODO: Consider making execution steps faux-immutable too.
    status: StatusLiteral
    exception: Optional[Exception]
    xcresult_path: Optional[pathlib.Path]
    trace_path: Optional[pathlib.Path]

    model_config = ConfigDict(
        frozen=True,  # Makes the model faux-immutable
        arbitrary_types_allowed=True,  # Required for the exception attribute
    )


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
        self.__trace_path: Optional[pathlib.Path] = None
        self.__xcresult_path: Optional[pathlib.Path] = None

    @property
    def status(self) -> StatusLiteral:
        return self.__status

    @property
    def execution_step(self) -> ExecutionStep:
        return self.__execution_step

    @property
    def exception(self) -> Optional[Exception]:
        return self.__exception

    @property
    def trace_path(self) -> Optional[pathlib.Path]:
        return self.__trace_path

    @property
    def xcresult_path(self) -> Optional[pathlib.Path]:
        return self.__xcresult_path

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

    def set_cancelled(self):
        """
        Set the status to cancelled.

        :raises ValueError: If the status is completed or failed.
        """
        if self.__status in ["completed", "failed"]:
            raise ValueError("Cannot set cancelled after completed or failed.")
        self.__status = "cancelled"

    def set_trace_path(self, trace_path: pathlib.Path):
        self.__trace_path = trace_path

    def set_xcresult_path(self, xcresult_path: pathlib.Path):
        self.__xcresult_path = xcresult_path

    def snapshot(self) -> ExecutionStepStateSnapshot:
        """
        Get a snapshot of the current state of the execution step.

        :return: The snapshot of the execution step state.
        """
        return ExecutionStepStateSnapshot(
            execution_step=self.__execution_step,
            status=self.__status,
            exception=self.__exception,
            trace_path=self.__trace_path,
            xcresult_path=self.__xcresult_path,
        )


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
        self.__current_execution_step_index += 1
        if self.__current_execution_step_index >= self.total_execution_steps:
            raise IndexError("No more execution steps left.")

        execution_step = self.__execution_plan.execution_steps[
            self.__current_execution_step_index
        ]

        execution_step_state = ExecutionStepState(
            execution_step=execution_step,
        )

        self.__execution_step_states[
            hash_session_execution_step(self.__session_id, execution_step)
        ] = execution_step_state

        return execution_step_state

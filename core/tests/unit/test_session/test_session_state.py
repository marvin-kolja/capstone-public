import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from core.test_session.execution_plan import ExecutionPlan, ExecutionStep
from core.test_session.plan import PlanStep, StepTestCase
from core.test_session.session_state import SessionState, ExecutionStepState


class TestSessionState:
    def test_init(self, mock_execution_plan):
        """
        GIVEN: A valid execution plan

        WHEN: SessionState is initialized.

        THEN: The state should be initialized correctly.
        """
        session_id = uuid.uuid4()

        session_state = SessionState(
            execution_plan=mock_execution_plan,
            session_id=session_id,
        )

        assert session_state._SessionState__execution_plan == mock_execution_plan
        assert session_state._SessionState__session_id == session_id
        assert session_state._SessionState__execution_step_states == {}
        assert session_state._SessionState__current_execution_step_index == -1

    def test_next_execution_step_valid(self, mock_execution_plan):
        """
        GIVEN: A new session state with a valid execution plan.

        WHEN: next_execution_step is called.

        THEN: The next execution step state is returned
        AND: The current execution step index is incremented.
        AND: The returned execution step state is stored in the execution step states dictionary.
        """
        session_id = uuid.uuid4()
        mock_execution_step = MagicMock(
            spec=ExecutionStep,
            plan_step_order=1,
            plan_repetition=0,
            step_repetition=0,
            test_cases=[
                MagicMock(
                    spec=StepTestCase,
                    xctest_id="Test",
                )
            ],
        )
        mock_execution_plan.execution_steps = [mock_execution_step]

        session_state = SessionState(
            execution_plan=mock_execution_plan,
            session_id=session_id,
        )

        execution_step_state = session_state.next_execution_step()

        assert execution_step_state.execution_step == mock_execution_step
        assert session_state._SessionState__current_execution_step_index == 0
        assert (
            execution_step_state
            in session_state._SessionState__execution_step_states.values()
        )

    def test_next_execution_step_index_out_of_bounds(self):
        """
        GIVEN: A session state with a valid execution plan
        AND: There are no more execution steps left.

        WHEN: next_execution_step is called.

        THEN: IndexError is raised.
        """
        session_id = uuid.uuid4()
        mock_execution_plan = MagicMock(
            spec=ExecutionPlan,
            execution_steps=[],
        )

        session_state = SessionState(
            execution_plan=mock_execution_plan,
            session_id=session_id,
        )

        with pytest.raises(IndexError):
            session_state.next_execution_step()


@pytest.fixture
def mock_execution_step():
    return MagicMock(
        spec=ExecutionStep,
        step=MagicMock(spec=PlanStep, order=1, name="Test"),
    )


class TestExecutionStepState:
    def test_init(self):
        """
        GIVEN: A valid execution step

        WHEN: ExecutionStepState is initialized.

        THEN: The state should be initialized correctly.
        """
        execution_step = MagicMock(
            spec=ExecutionStep,
            step=MagicMock(spec=PlanStep, order=1, name="Test"),
        )

        execution_step_state = ExecutionStepState(execution_step=execution_step)

        assert (
            execution_step_state._ExecutionStepState__execution_step == execution_step
        )
        assert execution_step_state.status == "not_started"
        assert execution_step_state.exception is None

    def test_set_running(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: set_running is called.

        THEN: The status should be set to running.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)

        execution_step_state.set_running()

        assert execution_step_state.status == "running"

    def test_set_running_after_completed_or_failed(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: status is completed or failed.
        AND: set_running is called.

        THEN: It should raise a ValueError.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)

        for status in ["completed", "failed"]:
            execution_step_state._ExecutionStepState__status = status
            with pytest.raises(ValueError):
                execution_step_state.set_running()

    def test_set_completed(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: set_completed is called.

        THEN: The status should be set to completed.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)

        execution_step_state.set_completed()

        assert execution_step_state.status == "completed"

    def test_set_completed_after_failed(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: status is failed.
        AND: set_completed is called.

        THEN: It should raise a ValueError.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)
        execution_step_state._ExecutionStepState__status = "failed"

        with pytest.raises(ValueError):
            execution_step_state.set_completed()

    def test_set_failed(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: set_failed is called with an exception.

        THEN: The status should be set to failed.
        AND: The exception should be stored.
        """
        exception = Exception("Test")
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)

        execution_step_state.set_failed(exception)

        assert execution_step_state.status == "failed"
        assert execution_step_state.exception == exception

    def test_set_failed_after_completed(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: status is completed.
        AND: set_failed is called with an exception.

        THEN: It should raise a ValueError.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)
        execution_step_state._ExecutionStepState__status = "completed"

        with pytest.raises(ValueError):
            execution_step_state.set_failed(Exception("Test"))

    def test_set_cancelled(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: set_cancelled is called.

        THEN: The status should be set to cancelled.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)

        execution_step_state.set_cancelled()

        assert execution_step_state.status == "cancelled"

    def test_set_cancelled_after_finished(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: status is completed or failed.
        AND: set_cancelled is called.

        THEN: It should raise a ValueError.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)

        for status in ["completed", "failed"]:
            execution_step_state._ExecutionStepState__status = status
            with pytest.raises(ValueError):
                execution_step_state.set_cancelled()

    @pytest.mark.parametrize(
        "status, exception",
        [
            ("not_started", None),
            ("running", None),
            ("completed", None),
            ("failed", Exception("Test")),
            ("cancelled", None),
        ],
    )
    def test_snapshot_creation(self, mock_execution_step, status, exception):
        """
        GIVEN: A new execution step state

        WHEN: snapshot is called.

        THEN: A snapshot of the current state should be returned.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)
        execution_step_state._ExecutionStepState__status = status
        execution_step_state._ExecutionStepState__exception = exception

        snapshot = execution_step_state.snapshot()

        assert snapshot.execution_step == mock_execution_step
        assert snapshot.status == status
        assert snapshot.exception == exception

    def test_snapshot_immutable(self, mock_execution_step):
        """
        GIVEN: A new execution step state

        WHEN: snapshot is called.

        THEN: The snapshot should be immutable.
        """
        execution_step_state = ExecutionStepState(execution_step=mock_execution_step)
        execution_step_state._ExecutionStepState__status = "completed"
        execution_step_state._ExecutionStepState__exception = Exception("Test")

        snapshot = execution_step_state.snapshot()

        with pytest.raises(ValidationError) as exc_info:
            snapshot.status = "running"
        assert exc_info.value.errors()[0]["loc"] == ("status",)
        assert exc_info.value.errors()[0]["msg"] == "Instance is frozen"
        assert exc_info.value.errors()[0]["type"] == "frozen_instance"

        with pytest.raises(ValidationError) as exc_info:
            snapshot.exception = None
        assert exc_info.value.errors()[0]["loc"] == ("exception",)
        assert exc_info.value.errors()[0]["msg"] == "Instance is frozen"
        assert exc_info.value.errors()[0]["type"] == "frozen_instance"

        with pytest.raises(ValidationError) as exc_info:
            snapshot.execution_step = MagicMock()
        assert exc_info.value.errors()[0]["loc"] == ("execution_step",)
        assert exc_info.value.errors()[0]["msg"] == "Instance is frozen"
        assert exc_info.value.errors()[0]["type"] == "frozen_instance"

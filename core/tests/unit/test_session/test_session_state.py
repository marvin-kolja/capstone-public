import uuid
from unittest.mock import MagicMock

import pytest

from core.test_session.execution_plan import ExecutionPlan, ExecutionStep
from core.test_session.plan import PlanStep
from core.test_session.session_state import SessionState


@pytest.fixture
def mock_execution_plan():
    return MagicMock(
        spec=ExecutionPlan,
        execution_steps=[],
    )


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

        assert session_state._execution_plan == mock_execution_plan
        assert session_state._session_id == session_id
        assert session_state._execution_step_states == {}
        assert session_state._current_execution_step_index == -1

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
            step=MagicMock(spec=PlanStep, order=1, name="Test"),
        )
        mock_execution_plan.execution_steps = [mock_execution_step]

        session_state = SessionState(
            execution_plan=mock_execution_plan,
            session_id=session_id,
        )

        execution_step_state = session_state.next_execution_step()

        assert execution_step_state.execution_step == mock_execution_plan
        assert session_state._current_execution_step_index == 0
        assert mock_execution_plan in session_state._execution_step_states.values()

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

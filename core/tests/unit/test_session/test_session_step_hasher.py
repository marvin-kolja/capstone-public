import uuid
from unittest.mock import MagicMock, patch

import pytest

from core.test_session.execution_plan import ExecutionStep
from core.test_session.plan import PlanStep, StepTestCase
from core.test_session.session_step_hasher import hash_session_execution_step


@pytest.fixture
def mock_execution_step():
    return MagicMock(
        spec=ExecutionStep,
        step=MagicMock(spec=PlanStep, order=1, name="Test"),
    )


class TestSessionStepHasher:
    @pytest.mark.parametrize("plan_repetition", [0, 1])
    @pytest.mark.parametrize("step_order", [0, 1])
    @pytest.mark.parametrize("step_repetition", [0, 1])
    @pytest.mark.parametrize("test_case_ids", [("id1", "id2"), ("id3",)])
    def test_hash_session_execution_step_input_string(
        self,
        mock_execution_step,
        plan_repetition,
        step_order,
        step_repetition,
        test_case_ids,
    ):
        """
        GIVEN a session id and an execution step

        WHEN the execution step hash is called with the session id and the

        THEN the input string that is hashed is the session id, plan repetition, step order, step repetition, and
        optionally test case id
        """
        session_id = uuid.uuid4()
        mock_execution_step.plan_repetition = plan_repetition
        mock_execution_step.step.order = step_order
        mock_execution_step.step_repetition = step_repetition
        mock_execution_step.test_cases = [
            MagicMock(spec=StepTestCase, xctest_id=x) for x in test_case_ids
        ]

        with patch("core.test_session.session_step_hasher.Hasher.hash") as mock_hash:
            hash_session_execution_step(session_id, mock_execution_step)
            if len(test_case_ids) == 1:
                mock_hash.assert_called_with(
                    f"{session_id}/{plan_repetition}/{step_order}/{step_repetition}/{test_case_ids[0]}"
                )
            else:
                mock_hash.assert_called_with(
                    f"{session_id}/{plan_repetition}/{step_order}/{step_repetition}"
                )

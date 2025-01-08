from unittest.mock import MagicMock

import pytest

from core.test_session.execution_plan import ExecutionPlan, ExecutionStep
from core.test_session.metrics import Metric
from core.test_session.plan import (
    SessionTestPlan,
    XctestrunConfig,
    StepTestCase,
    PlanStep,
)
from core.test_session.xctestrun import XcTestTarget


@pytest.fixture
def mock_test_plan():
    return MagicMock(
        spec=SessionTestPlan,
        recording_strategy="per_step",
        reinstall_app=False,
        metrics=[Metric.cpu, Metric.fps],
        end_on_failure=True,
        xctestrun_config=MagicMock(
            spec=XctestrunConfig,
            path="example.xctestrun",
        ),
    )


@pytest.fixture
def mock_step():
    return MagicMock(
        spec=PlanStep,
        reinstall_app=True,
        metrics=None,
        test_cases=[
            MagicMock(
                spec=StepTestCase,
            ),
        ],
        recording_start_strategy="launch",
    )


@pytest.fixture
def mock_xc_test_targets():
    return {"target_1": MagicMock(spec=XcTestTarget)}


@pytest.fixture
def mock_execution_plan():
    return MagicMock(
        spec=ExecutionPlan,
        execution_steps=[],
    )


@pytest.fixture
def mock_execution_step():
    return MagicMock(
        spec=ExecutionStep,
        step=MagicMock(spec=PlanStep, order=1, name="Test"),
    )

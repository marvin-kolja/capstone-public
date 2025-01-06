import pytest
from pydantic import ValidationError
from core.test_session.metrics import Metric
from core.test_session.plan import (
    SessionTestPlan,
    PlanStep,
    StepTestCase,
    XctestrunConfig,
)


@pytest.fixture
def fake_xctestrun_config():
    return XctestrunConfig(path="path", test_configuration="config")


class TestSessionTestPlan:
    def test_valid_test_plan(self, fake_xctestrun_config):
        """
        GIVEN a valid SessionTestPlan with ordered steps

        WHEN the SessionTestPlan is validated

        THEN it should pass without errors
        """
        valid_test_plan = SessionTestPlan(
            name="Valid Test Plan",
            repetitions=2,
            repetition_strategy="entire_suite",
            metrics=[Metric.cpu],
            recording_strategy="per_step",
            recording_start_strategy="launch",
            reinstall_app=False,
            steps=[
                PlanStep(order=0, test_cases=[StepTestCase(xctest_id="test_1")]),
                PlanStep(order=1, test_cases=[StepTestCase(xctest_id="test_2")]),
            ],
            xctestrun_config=fake_xctestrun_config,
        )
        assert valid_test_plan.name == "Valid Test Plan"

    def test_unordered_steps(self, fake_xctestrun_config):
        """
        GIVEN a SessionTestPlan with unordered steps

        WHEN the SessionTestPlan is validated

        THEN it should not raise a ValidationError
        AND the steps should be ordered
        """
        test_plan = SessionTestPlan(
            name="Unordered Steps",
            repetitions=1,
            repetition_strategy="entire_suite",
            metrics=[Metric.cpu],
            recording_strategy="per_step",
            recording_start_strategy="launch",
            reinstall_app=False,
            steps=[
                PlanStep(order=1, test_cases=[StepTestCase(xctest_id="test_1")]),
                PlanStep(order=0, test_cases=[StepTestCase(xctest_id="test_2")]),
                PlanStep(order=2, test_cases=[StepTestCase(xctest_id="test_3")]),
            ],
            xctestrun_config=fake_xctestrun_config,
        )

        assert test_plan.steps[0].order == 0
        assert test_plan.steps[1].order == 1
        assert test_plan.steps[2].order == 2

    def test_invalid_step_order_sequence(self, fake_xctestrun_config):
        """
        GIVEN a SessionTestPlan with invalid step order sequence

        WHEN the SessionTestPlan is created

        THEN it should raise a ValidationError
        """
        with pytest.raises(ValidationError, match="Step order is not sequential"):
            SessionTestPlan(
                name="Invalid Step Order",
                repetitions=1,
                repetition_strategy="entire_suite",
                metrics=[Metric.cpu],
                recording_strategy="per_step",
                recording_start_strategy="launch",
                reinstall_app=False,
                steps=[
                    PlanStep(order=0, test_cases=[StepTestCase(xctest_id="test_1")]),
                    PlanStep(order=2, test_cases=[StepTestCase(xctest_id="test_2")]),
                ],
                xctestrun_config=fake_xctestrun_config,
            )

    def test_invalid_repetitions(self, fake_xctestrun_config):
        """
        GIVEN a SessionTestPlan with an invalid repetition count

        WHEN the SessionTestPlan is created

        THEN it should raise a ValidationError
        """
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            SessionTestPlan(
                name="Invalid Repetitions",
                repetitions=0,
                repetition_strategy="entire_suite",
                metrics=[Metric.cpu],
                recording_strategy="per_step",
                recording_start_strategy="launch",
                reinstall_app=False,
                steps=[
                    PlanStep(order=0, test_cases=[StepTestCase(xctest_id="test_1")])
                ],
                xctestrun_config=fake_xctestrun_config,
            )

    def test_missing_steps(self, fake_xctestrun_config):
        """
        GIVEN a SessionTestPlan with missing steps

        WHEN the SessionTestPlan is created

        THEN it should raise a ValidationError
        """
        with pytest.raises(
            ValidationError,
            match="List should have at least 1 item after validation, not 0",
        ):
            SessionTestPlan(
                name="Missing Steps",
                repetitions=1,
                repetition_strategy="entire_suite",
                metrics=[Metric.cpu],
                recording_strategy="per_step",
                recording_start_strategy="launch",
                reinstall_app=False,
                steps=[],
                xctestrun_config=fake_xctestrun_config,
            )

    def test_invalid_step_order(self):
        """
        GIVEN a TestStep with an invalid order

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            PlanStep(order=-1, test_cases=[StepTestCase(xctest_id="test_1")])

    def test_invalid_step_repetitions(self):
        """
        GIVEN a TestStep with repetitions less than 1

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            PlanStep(
                order=0, repetitions=0, test_cases=[StepTestCase(xctest_id="test_1")]
            )

    def test_missing_test_cases(self):
        """
        GIVEN a TestStep with missing test cases

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            PlanStep(order=0, test_cases=None)

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


@pytest.fixture
def fake_valid_test_cases():
    return [
        StepTestCase(xctest_id="TestTarget/TestClass/testMethod"),
        StepTestCase(xctest_id="TestTarget/TestClass/testMethod2"),
    ]


class TestSessionTestPlan:
    def test_valid_test_plan(self, fake_xctestrun_config, fake_valid_test_cases):
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
                PlanStep(order=0, test_cases=fake_valid_test_cases),
                PlanStep(order=1, test_cases=fake_valid_test_cases),
            ],
            xctestrun_config=fake_xctestrun_config,
        )
        assert valid_test_plan.name == "Valid Test Plan"

    def test_unordered_steps(self, fake_xctestrun_config, fake_valid_test_cases):
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
                PlanStep(order=1, test_cases=fake_valid_test_cases),
                PlanStep(order=0, test_cases=fake_valid_test_cases),
                PlanStep(order=2, test_cases=fake_valid_test_cases),
            ],
            xctestrun_config=fake_xctestrun_config,
        )

        assert test_plan.steps[0].order == 0
        assert test_plan.steps[1].order == 1
        assert test_plan.steps[2].order == 2

    def test_invalid_step_order_sequence(
        self, fake_xctestrun_config, fake_valid_test_cases
    ):
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
                    PlanStep(order=0, test_cases=fake_valid_test_cases),
                    PlanStep(order=2, test_cases=fake_valid_test_cases),
                ],
                xctestrun_config=fake_xctestrun_config,
            )

    def test_invalid_repetitions(self, fake_xctestrun_config, fake_valid_test_cases):
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
                steps=[PlanStep(order=0, test_cases=fake_valid_test_cases)],
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

    def test_test_cases_with_different_test_targets(self):
        """
        GIVEN a list of StepTestCases with different test targets

        WHEN the PlanStep is created

        THEN it should raise a ValidationError
        """
        test_cases = [
            StepTestCase(xctest_id="TestTarget/TestClass/testMethod"),
            StepTestCase(xctest_id="TestTarget2/TestClass/testMethod"),
        ]

        with pytest.raises(
            ValidationError,
            match="All test cases in a step must be from the same test target",
        ):
            PlanStep(order=0, test_cases=test_cases)

    def test_invalid_step_order(self, fake_valid_test_cases):
        """
        GIVEN a TestStep with an invalid order

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 0"
        ):
            PlanStep(order=-1, test_cases=fake_valid_test_cases)

    def test_invalid_step_repetitions(self, fake_valid_test_cases):
        """
        GIVEN a TestStep with repetitions less than 1

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(
            ValidationError, match="Input should be greater than or equal to 1"
        ):
            PlanStep(order=0, repetitions=0, test_cases=fake_valid_test_cases)

    def test_missing_test_cases(self):
        """
        GIVEN a TestStep with missing test cases

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            PlanStep(order=0, test_cases=None)

    def test_validating_test_case_invalid_format(self):
        """
        GIVEN a TestStep with an invalid test case format

        WHEN the TestStep is validated

        THEN it should raise a ValidationError
        """
        with pytest.raises(ValidationError, match="expected 3 parts"):
            StepTestCase(xctest_id="InvalidFormat")

    def test_validating_test_case_valid_format(self):
        """
        GIVEN a TestStep with a valid test case format

        WHEN the TestStep is validated

        THEN it should pass without errors
        """
        StepTestCase(xctest_id="TestTarget/TestClass/testMethod")

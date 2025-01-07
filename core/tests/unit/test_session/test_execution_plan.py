from unittest.mock import patch

import pytest

from core.test_session.execution_plan import ExecutionPlan
from core.test_session.metrics import Metric
from core.test_session.plan import (
    SessionTestPlan,
    XctestrunConfig,
    PlanStep,
    StepTestCase,
)


class TestExecutionPlan:
    def test_convert_test_targets_to_dict(self, example_xctestrun):
        """
        GIVEN: A XcTestConfiguration object

        WHEN: _convert_test_targets_to_dict is called

        THEN: The test targets should be converted to a dictionary correctly
        """
        test_configuration = example_xctestrun.TestConfigurations[0]

        test_targets = ExecutionPlan._convert_test_targets_to_dict(test_configuration)

        assert len(test_targets) == 2
        assert "PlaceholderTests" in test_targets
        assert "PlaceholderUITests" in test_targets

        assert test_targets["PlaceholderTests"].BlueprintName == "PlaceholderTests"
        assert test_targets["PlaceholderUITests"].BlueprintName == "PlaceholderUITests"

    def test_extract_info_plist(self, example_xctestrun):
        """
        GIVEN: A list of XcTestTarget objects

        WHEN: _extract_info_plists is called

        THEN: The `parse_plist` method should be called with the correct path to the Info.plist file for each target the
        right amount of times
        """
        test_configuration = example_xctestrun.TestConfigurations[0]

        with patch("core.app.xc_app.read_plist") as mock_read_plist, patch(
            "core.app.xc_app.InfoPlist.model_validate", return_value=None
        ) as mock_info_plist_model_validate:
            info_plists = ExecutionPlan._extract_info_plists(
                test_configuration.TestTargets
            )

            assert len(info_plists) == 2
            assert mock_read_plist.call_count == 2
            assert mock_info_plist_model_validate.call_count == 2

            for TestTarget in test_configuration.TestTargets:
                assert TestTarget.app_path in info_plists
                mock_read_plist.assert_any_call(TestTarget.app_path + "/Info.plist")
                if TestTarget.ui_test_app_path:
                    assert TestTarget.ui_test_app_path in info_plists
                    mock_read_plist.assert_any_call(
                        TestTarget.ui_test_app_path + "/Info.plist"
                    )

    @pytest.mark.parametrize("recording_start_strategy", ["launch", "attach"])
    @pytest.mark.parametrize("repetition_strategy", ["entire_suite", "per_step"])
    @pytest.mark.parametrize("recording_strategy", ["per_step", "per_test"])
    @pytest.mark.parametrize("reinstall_app", [True, False])
    class TestParametrized:
        @pytest.fixture(autouse=True)
        def setup_test_plan(
            self,
            recording_start_strategy,
            repetition_strategy,
            recording_strategy,
            reinstall_app,
            example_xctestrun_path,
            example_xctestrun,
        ):
            """
            Creates a shared SessionTestPlan instance for all tests in this class.
            """
            self.session_test_plan = SessionTestPlan(
                xctestrun_config=XctestrunConfig(
                    path=example_xctestrun_path.absolute().as_posix(),
                    test_configuration="Test Scheme Action",  # This is based on the example xctestrun file
                ),
                recording_start_strategy=recording_start_strategy,
                repetition_strategy=repetition_strategy,
                recording_strategy=recording_strategy,
                reinstall_app=reinstall_app,
                metrics=[Metric.cpu, Metric.fps],
                repetitions=2,
                steps=[
                    PlanStep(
                        order=0,
                        repetitions=2,
                        reinstall_app=False,
                        test_cases=[
                            StepTestCase(
                                xctest_id="PlaceholderUITests/PlaceholderUITests/testExample",
                                # This is based on the example xctestrun file
                            ),
                            StepTestCase(
                                xctest_id="PlaceholderUITests/PlaceholderUITests/testExample2",
                                # This is based on the example xctestrun file
                            ),
                        ],
                    ),
                    PlanStep(
                        order=1,
                        repetitions=1,
                        reinstall_app=True,
                        test_cases=[
                            StepTestCase(
                                xctest_id="PlaceholderUITests/PlaceholderUITests/testLaunchPerformance",
                                # This is based on the example xctestrun file
                            ),
                        ],
                    ),
                ],
            )

        def test_plan_execution_steps(self, example_xctestrun):
            """
            GIVEN: A SessionTestPlan object

            WHEN: _plan_execution_steps is called

            THEN: The correct amount of ExecutionStep objects should be created based on the test plan
            AND: The order of the steps should be correct based on the repetition numbers
            """
            example_test_plan = self.session_test_plan

            test_configuration = example_xctestrun.TestConfigurations[0]
            execution_steps = ExecutionPlan._plan_execution_steps(
                example_test_plan,
                {
                    "PlaceholderTests": test_configuration.TestTargets[0],
                    "PlaceholderUITests": test_configuration.TestTargets[1],
                },
            )

            # Count validation
            if example_test_plan.recording_strategy == "per_step":
                expected_count = (
                    sum(step.repetitions for step in example_test_plan.steps)
                    * example_test_plan.repetitions
                )
                assert len(execution_steps) == expected_count, (
                    f"Expected {expected_count} steps for 'per_step', "
                    f"but got {len(execution_steps)}."
                )
            elif example_test_plan.recording_strategy == "per_test":
                expected_count = (
                    sum(
                        len(step.test_cases) * step.repetitions
                        for step in example_test_plan.steps
                    )
                    * example_test_plan.repetitions
                )
                assert len(execution_steps) == expected_count, (
                    f"Expected {expected_count} steps for 'per_test', "
                    f"but got {len(execution_steps)}."
                )

            # Make sure that the order of execution steps is correct based on the repetition strategy
            for idx, step in enumerate(execution_steps):
                previous_step = execution_steps[idx - 1] if idx > 0 else None

                if previous_step:
                    assert previous_step.plan_repetition <= step.plan_repetition, (
                        f"Step repetition should be in order, but got "
                        f"{previous_step.step_repetition} before {step.step_repetition}."
                    )
                    if previous_step.step == step.step:
                        assert previous_step.step_repetition <= step.step_repetition, (
                            f"Step repetition should be in order, but got "
                            f"{previous_step.step_repetition} before {step.step_repetition}."
                        )
                else:
                    assert (
                        step.plan_repetition == 0
                    ), "First step should have repetition 0."
                    assert (
                        step.step_repetition == 0
                    ), "First step should have repetition 0."

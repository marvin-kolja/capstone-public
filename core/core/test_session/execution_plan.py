from typing import Literal, Optional

from pydantic import BaseModel

from core.app.info_plist import InfoPlist
from core.app.xc_app import XcApp
from core.test_session.metrics import Metric
from core.test_session.plan import PlanStep, StepTestCase, SessionTestPlan
from core.test_session.xctest import Xctest
from core.test_session.xctestrun import XcTestTarget, Xctestrun, XcTestConfiguration


class ExecutionStep(BaseModel):
    """
    Instructions for a single execution step in the test session.

    Not to be confused with `PlanStep` which is a step in the test plan. This step is derived from the test plan step
    but does not represent a `PlanStep` instance.
    """

    plan_repetition: int
    """The repetition of the test plan that this step belongs to."""
    step: PlanStep
    """The test plan step that this execution step is derived from."""
    step_repetition: int
    """The repetition of the test plan step."""
    recording_start_strategy: Literal["launch", "attach"]
    reinstall_app: bool
    metrics: list[Metric]
    test_cases: list[StepTestCase]
    end_on_failure: bool
    test_target: XcTestTarget
    """The test target that this step is associated with."""


class ExecutionPlan:
    """
    This class is responsible for planning the execution steps of the test session based on the test plan.

    Attributes:
        test_plan (SessionTestPlan): The test plan to execute.
        execution_steps (list[ExecutionStep]): The list of execution steps that must be performed in order.
        xctestrun (Xctestrun): The parsed xctestrun file.
        xc_test_targets (dict[str, XcTestTarget]): A dictionary of test targets extracted from the xctestrun file where
            the key is the test target name.
        info_plists (dict[str, InfoPlist]): A dictionary of info plists extracted from the xctestrun file where the key
            is the path to the package containing the `Info.plist` file.
    """

    def __init__(self, test_plan: SessionTestPlan):
        """
        :param test_plan: The test plan to execute.
        """
        self.test_plan = test_plan.model_copy(
            deep=True
        )  # Copy the test plan to avoid modifications during planning from outside
        self.execution_steps: Optional[list[ExecutionStep]] = None
        self.xctestrun: Optional[Xctestrun] = None
        self.xc_test_targets: Optional[dict[str, XcTestTarget]] = None
        self.info_plists: Optional[dict[str, InfoPlist]] = None

    def plan(self):
        """
        Plans the steps to be executed in the test session based on the test plan.

        * Parse the xctestrun file
        * Extract the test configuration and its targets
        * Extract the info plists
        * Plan the execution steps
        """
        xctestrun_config = self.test_plan.xctestrun_config
        self.xctestrun = Xctest.parse_xctestrun(xctestrun_config.path)
        xc_test_configuration = self.xctestrun.extract_test_configuration_with_name(
            xctestrun_config.test_configuration
        )
        self.xc_test_targets = self._convert_test_targets_to_dict(xc_test_configuration)
        self.info_plists = self._extract_info_plists(
            list(self.xc_test_targets.values())
        )

        self.execution_steps = self._generate_execution_steps(
            self.test_plan, self.xc_test_targets
        )

    @staticmethod
    def _generate_execution_steps(
        test_plan: SessionTestPlan, xc_test_targets: dict[str, XcTestTarget]
    ) -> list[ExecutionStep]:
        """
        Plan the execution steps based on the test plan. This will generate a list of `ExecutionStep` that
        represent the steps to be executed in the test session.
        """
        execution_steps: list[ExecutionStep] = []

        if test_plan.repetition_strategy == "entire_suite":
            for repetition in range(test_plan.repetitions):
                for step in test_plan.steps:
                    for step_repetition in range(step.repetitions):
                        execution_steps.extend(
                            ExecutionPlan._generate_plan_step_execution_steps(
                                test_plan=test_plan,
                                step=step,
                                step_repetition=step_repetition,
                                repetition=repetition,
                                xc_test_targets=xc_test_targets,
                            )
                        )
        elif test_plan.repetition_strategy == "per_step":
            for step in test_plan.steps:
                repetitions = step.repetitions * test_plan.repetitions
                for current_repetition in range(repetitions):
                    execution_steps.extend(
                        ExecutionPlan._generate_plan_step_execution_steps(
                            test_plan=test_plan,
                            step=step,
                            step_repetition=current_repetition,
                            repetition=0,
                            xc_test_targets=xc_test_targets,
                        )
                    )
        else:
            raise ValueError(
                f"Invalid repetition strategy: {test_plan.repetition_strategy}"
            )
        return execution_steps

    @staticmethod
    def _generate_plan_step_execution_steps(
        test_plan: SessionTestPlan,
        step: PlanStep,
        repetition: int,
        step_repetition: int,
        xc_test_targets: dict[str, XcTestTarget],
    ) -> list[ExecutionStep]:
        """
        Generate the execution steps for a single test plan step based on the test plan, step, xc test targets, and
        repetitions.
        """
        execution_steps: list[ExecutionStep] = []
        recording_strategy = test_plan.recording_strategy

        # Determine correct recording start strategy
        #
        # This is never None, but IntelliJ does not seem to understand that
        # noinspection PyTypeChecker
        recording_start_strategy: Literal["launch", "attach"] = (
            step.recording_start_strategy or test_plan.recording_start_strategy
        )

        # Determine correct reinstall app strategy
        reinstall_app = (
            step.reinstall_app
            if step.reinstall_app is not None
            else test_plan.reinstall_app
        )

        # Determine correct metrics
        metrics = step.metrics if step.metrics is not None else test_plan.metrics

        # NOTE: We assume that all test cases in a step are from the same test target here as test cases are validated
        # that way. Thus, we can safely get the test target name from the first test case.
        test_target_name = step.test_cases[0].test_target

        if (test_target := xc_test_targets.get(test_target_name)) is None:
            raise ValueError(
                f"Test target '{test_target_name}' not found in xctestrun file {test_plan.xctestrun_config.path}"
            )

        if recording_strategy == "per_step":
            execution_steps.append(
                ExecutionStep(
                    plan_repetition=repetition,
                    step=step,
                    step_repetition=step_repetition,
                    recording_start_strategy=recording_start_strategy,
                    reinstall_app=reinstall_app,
                    metrics=metrics,
                    test_cases=step.test_cases,
                    end_on_failure=test_plan.end_on_failure,
                    test_target=test_target,
                )
            )
        elif recording_strategy == "per_test":
            for idx, test_case in enumerate(step.test_cases):
                first_in_step = idx == 0
                should_reinstall_app = first_in_step and reinstall_app
                # Ensure the app is reinstalled ONLY once per step, if required

                execution_steps.append(
                    ExecutionStep(
                        plan_repetition=repetition,
                        step=step,
                        step_repetition=step_repetition,
                        recording_start_strategy=recording_start_strategy,
                        reinstall_app=should_reinstall_app,
                        metrics=metrics,
                        test_cases=[test_case],
                        end_on_failure=test_plan.end_on_failure,
                        test_target=test_target,
                    )
                )

        return execution_steps

    @staticmethod
    def _convert_test_targets_to_dict(
        xc_test_configuration: XcTestConfiguration,
    ) -> dict[str, XcTestTarget]:
        """
        Convert the list of test targets in the test configuration to a dictionary.

        :param xc_test_configuration: The test configuration to extract the test targets from.
        """
        test_targets: dict[str, XcTestTarget] = {}

        for test_target in xc_test_configuration.TestTargets:
            # BlueprintName is the name of the test target and can be used to identify if xctest ids have a valid test
            # suite name.
            test_targets[test_target.BlueprintName] = test_target

        return test_targets

    @staticmethod
    def _extract_info_plists(test_targets: list[XcTestTarget]) -> dict[str, InfoPlist]:
        """
        Extract the info plists from the test targets and return them as a dictionary where the key is the path to the
        package containing the `Info.plist` file.

        :param test_targets: The test targets to extract the info plists from.
        """

        info_plists: dict[str, InfoPlist] = {}

        for test_target in test_targets:
            target_app = XcApp(test_target.app_path)

            if target_app.path not in info_plists:
                info_plist = target_app.parse_info_plist()
                info_plists[target_app.path] = info_plist

            if test_target.ui_test_app_path is not None:
                ui_test_app = XcApp(test_target.ui_test_app_path)
                if ui_test_app.path not in info_plists:
                    ui_info_plist = ui_test_app.parse_info_plist()
                    info_plists[ui_test_app.path] = ui_info_plist

        return info_plists

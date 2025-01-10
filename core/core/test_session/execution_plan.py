import logging
from typing import Literal, Optional

from pydantic import BaseModel

from core.xc.app_bundle.info_plist import InfoPlist
from core.xc.app_bundle.bundle_interface import AppBundle
from core.xc.commands.xctrace_command import Instrument
from core.test_session.metrics import Metric, parse_metrics_to_instruments
from core.test_session.plan import (
    PlanStep,
    StepTestCase,
    SessionTestPlan,
    XctestrunConfig,
)
from core.xc.xctest import Xctest
from core.xc.xctestrun import XcTestTarget, Xctestrun, XcTestConfiguration

logger = logging.getLogger(__name__)


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
    xctestrun_config: XctestrunConfig
    """The xctestrun configuration of the test plan."""

    @property
    def xctest_ids(self) -> list[str]:
        """
        :return: the xctest ids of the ``test_cases`` in the step.
        """
        return [test_case.xctest_id for test_case in self.test_cases]

    @property
    def instruments(self) -> list[Instrument]:
        """
        :return: the instruments to be used for this step based on the metrics.
        """
        return parse_metrics_to_instruments(self.metrics)


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
        logger.info(
            f"Starting to plan execution steps for the test plan: {self.test_plan.name}"
        )
        xctestrun_config = self.test_plan.xctestrun_config
        xctestrun_path = xctestrun_config.path
        x_test_configuration_name = xctestrun_config.test_configuration

        self.xctestrun = Xctest.parse_xctestrun(xctestrun_path)
        logger.debug(
            f"Xctestrun file parsed: {xctestrun_path} for test plan {self.test_plan.name}"
        )

        try:
            xc_test_configuration = self.xctestrun.extract_test_configuration_with_name(
                x_test_configuration_name
            )
        except ValueError:
            logger.error(
                f"Test configuration '{x_test_configuration_name}' not found in xctestrun file {xctestrun_path}"
            )
            raise
        logger.debug(
            f"Test configuration '{x_test_configuration_name}' extracted from xctestrun file {xctestrun_path}"
        )

        self.xc_test_targets = self._convert_test_targets_to_dict(xc_test_configuration)

        logger.debug(
            f"Extracted test targets from xctestrun file {xctestrun_path} using test configuration "
            f"'{x_test_configuration_name}': {list(self.xc_test_targets.keys())}"
        )

        self.info_plists = self._extract_info_plists(
            list(self.xc_test_targets.values())
        )

        logger.debug(
            f"Extracted Info plists from xctestrun file {xctestrun_path} for test targets: "
            f"{list(self.info_plists.keys())}"
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
        logger.info(
            f"Generating execution steps for test plan: {test_plan.name} with {len(test_plan.steps)} steps"
        )

        execution_steps: list[ExecutionStep] = []

        if test_plan.repetition_strategy == "entire_suite":
            logger.debug(
                f"Repetition strategy is 'entire_suite', generating execution steps for the entire suite"
            )

            for repetition in range(test_plan.repetitions):
                for step in test_plan.steps:
                    for step_repetition in range(step.repetitions):
                        logger.debug(
                            f"Generating execution steps for step '{step.name}' with plan repetition '{repetition}' and "
                            f"step repetition '{step_repetition}'"
                        )
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
            logger.debug(
                f"Repetition strategy is 'per_step', generating execution steps for each step"
            )

            for step in test_plan.steps:
                repetitions = step.repetitions * test_plan.repetitions
                for current_repetition in range(repetitions):
                    logger.debug(
                        f"Generating execution steps for step '{step.name}' with repetition {current_repetition}"
                    )
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
            err_msg = f"Invalid repetition strategy: {test_plan.repetition_strategy} for test plan {test_plan.name}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.info(
            f"Generated {len(execution_steps)} execution steps for test plan: {test_plan.name}"
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

        :raises ValueError: If the test target is not found in the xctestrun file or if the recording strategy is
        invalid.
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
        logger.debug(
            f"Recording start strategy for step '{step.name}' is '{recording_start_strategy}'"
        )

        # Determine correct reinstall app strategy
        reinstall_app = (
            step.reinstall_app
            if step.reinstall_app is not None
            else test_plan.reinstall_app
        )
        logger.debug(
            f"Reinstall app strategy for step '{step.name}' is '{reinstall_app}'"
        )
        if repetition == 0 and step_repetition == 0:
            reinstall_app = True
            logger.debug(
                f"Reinstall app strategy for step '{step.name}' is forced to 'True' as this is the first step"
            )

        # Determine correct metrics
        metrics = step.metrics if step.metrics is not None else test_plan.metrics
        logger.debug(f"Metrics for step '{step.name}' are '{metrics}'")

        # NOTE: We assume that all test cases in a step are from the same test target here as test cases are validated
        # that way. Thus, we can safely get the test target name from the first test case.
        test_target_name = step.test_cases[0].test_target
        logger.debug(f"Test target name for step '{step.name}' is '{test_target_name}'")

        if (test_target := xc_test_targets.get(test_target_name)) is None:
            err_msg = f"Test target '{test_target_name}' not found in xctestrun file {test_plan.xctestrun_config.path}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        if recording_strategy == "per_step":
            logger.debug(
                f"Recording strategy is 'per_step', adding a single execution step for the entire step '{step.name}'"
            )
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
                    xctestrun_config=test_plan.xctestrun_config,
                )
            )
        elif recording_strategy == "per_test":
            logger.debug(
                f"Recording strategy is 'per_test', looping through each test case in the step"
            )

            for idx, test_case in enumerate(step.test_cases):
                first_in_step = idx == 0
                should_reinstall_app = first_in_step and reinstall_app
                # Ensure the app is reinstalled ONLY once per step, if required

                logger.debug(
                    f"Adding execution step for test case '{test_case.xctest_id}' of step '{step.name}'"
                )
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
                        xctestrun_config=test_plan.xctestrun_config,
                    )
                )
        else:
            err_msg = f"Invalid recording strategy: {recording_strategy}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.debug(
            f"Generated {len(execution_steps)} execution steps for step '{step.name}'"
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
        logger.debug(f"Converting test targets to dictionary")

        test_targets: dict[str, XcTestTarget] = {}

        for test_target in xc_test_configuration.TestTargets:
            # BlueprintName is the name of the test target and can be used to identify if xctest ids have a valid test
            # suite name.
            logger.debug(
                f"Adding test target: {test_target.BlueprintName} to dictionary"
            )
            test_targets[test_target.BlueprintName] = test_target

        return test_targets

    @staticmethod
    def _extract_info_plists(test_targets: list[XcTestTarget]) -> dict[str, InfoPlist]:
        """
        Extract the info plists from the test targets and return them as a dictionary where the key is the path to the
        package containing the `Info.plist` file.

        :param test_targets: The test targets to extract the info plists from.
        """
        logger.debug(f"Extracting Info plists for {len(test_targets)} test targets")

        info_plists: dict[str, InfoPlist] = {}

        for test_target in test_targets:
            logger.debug(f"Extracting Info plists for test target: '{test_target}'")

            app_paths = [test_target.app_path]
            if test_target.ui_test_app_path is not None:
                app_paths.append(test_target.ui_test_app_path)

            for path in app_paths:
                if path not in info_plists:
                    logger.debug(f"Extracting Info plist for app: '{path}'")
                    app = AppBundle(path)
                    info_plist = app.parse_info_plist()
                    info_plists[path] = info_plist
                else:
                    logger.debug(f"Info plist for already extracted for app: '{path}'")

        return info_plists

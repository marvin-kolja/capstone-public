from typing import Literal, Optional

from pydantic import BaseModel

from core.app.info_plist import InfoPlist
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

        self.execution_steps = self._plan_execution_steps(
            self.test_plan, self.xc_test_targets
        )

    @staticmethod
    def _plan_execution_steps(
        test_plan: SessionTestPlan, xc_test_targets: dict[str, XcTestTarget]
    ) -> list[ExecutionStep]:
        """
        Plan the execution steps based on the test plan. This will create a list of `ExecutionStep` instances that
        represent the steps to be executed in the test session.
        """
        raise NotImplementedError

    @staticmethod
    def _convert_test_targets_to_dict(
        xc_test_configuration: XcTestConfiguration,
    ) -> dict[str, XcTestTarget]:
        """
        Convert the list of test targets in the test configuration to a dictionary.

        :param xc_test_configuration: The test configuration to extract the test targets from.
        """
        raise NotImplementedError

    @staticmethod
    def _extract_info_plists(test_targets: list[XcTestTarget]) -> dict[str, InfoPlist]:
        """
        Extract the info plists from the test targets and return them as a dictionary where the key is the path to the
        package containing the `Info.plist` file.

        :param test_targets: The test targets to extract the info plists from.
        """
        raise NotImplementedError

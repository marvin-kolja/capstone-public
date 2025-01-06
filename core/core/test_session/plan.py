from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

from core.test_session.metrics import Metric


class StepTestCase(BaseModel):
    xctest_id: str


class PlanStep(BaseModel):
    order: int = Field(ge=0)
    """Order of the step in the test plan."""

    name: Optional[str] = None
    """User defined name of the test step."""

    repetitions: Optional[int] = Field(ge=1, default=1)
    """
    Number of times the step should be repeated. This does not overwrite the repetitions of the test plan. Meaning, if
    the test plan has 3 repetitions and the step has 2 repetitions, the step will be executed 6 times in total.
    """

    test_cases: list[StepTestCase]
    """List of test cases to be executed in this step."""

    metrics: Optional[list[Metric]] = None
    """
    Metrics to be recorded for this step.
    
    Overrides the test plan metrics.
    
    If not provided, the global metrics will be used.
    
    If empty, no metrics will be recorded for this step.
    """

    recording_start_strategy: Optional[Literal["launch", "attach"]] = None
    """Overrides the test plan recording start strategy for this step."""

    reinstall_app: Optional[bool] = None
    """Overrides the test plan reinstall app strategy for this step."""


class XctestrunConfig(BaseModel):
    path: str
    """
    Path to the xctestrun file.
    """

    test_configuration: str
    """
    Name of test configuration to be used.
    """


class SessionTestPlan(BaseModel):
    name: Optional[str] = None
    """
    User defined name of the test plan.
    """

    xctestrun_config: XctestrunConfig
    """
    Information about the xctestrun file and the test configuration to be used.
    """

    end_on_failure: Optional[bool] = False
    """
    Whether the test plan should end on the first failure encountered.
    
    A failure is either a test failure or when recording of metrics fails.
    """

    repetitions: int = Field(ge=1)
    """
    Number of times the entire test plan should be repeated.
    """

    repetition_strategy: Literal["entire_suite", "per_step"]
    """
    Strategy to be used for repetitions. If 'entire_suite', the entire test plan will be repeated 'repetitions' times.
    If 'per_step', each step will be repeated 'repetitions' times.
    """

    metrics: list[Metric]
    """
    List of metrics to be recorded for the entire test plan.
    
    If empty, no metrics will be recorded.
    
    Each step can override this list by providing its own list of metrics.
    """

    recording_strategy: Literal["per_step", "per_test"] = "per_step"
    """
    How the metrics should be recorded. If ``per_step``, the metrics will be recorded for each step. If ``per_test``, the
    metrics will be recorded for each single test case of the steps.
    
    **WARNING:** ``per_test`` may introduce a noticeable overhead, as each test case will be executed and traced/recorded
    separately. If you have a test that terminates the app, thus, stopping the recording, it might make more sense to
    put it in a separate step and use ``per_step`` recording mode for better performance.
    """

    recording_start_strategy: Literal["launch", "attach"] = "launch"
    """
    How the recording of metrics should be started. If ``launch``, the app will be launched before the recording starts.
    If ``attach``, the recording will attach to the already running app process.
    
    This will also change how test cases are executed. If ``launch``, the app will be launched prior to the test
    execution. If ``attach``, the recording will attach as soon as the app is started by the executed test.
    """

    reinstall_app: bool = False
    """
    Whether the app should be reinstalled before each test step.
    
    Can be overridden by the test step.
    """

    steps: list[PlanStep] = Field(min_length=1)
    """
    List of test steps to be executed in this test plan.
    """

    @field_validator("steps", mode="after")
    def validate_order_of_steps(cls, steps):
        """
        Validates the order of the steps in the test plan.

        It orders the steps by their order and then checks if the order is sequential starting from 0 and increasing by
        1.
        """
        if not steps:
            return

        steps = sorted(steps, key=lambda x: x.order)

        for idx, step in enumerate(steps):
            if step.order != idx:
                raise ValueError(
                    f"Step order is not sequential. Expected {idx}, got {step.order}"
                )

        return steps

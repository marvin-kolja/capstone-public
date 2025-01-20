import logging
import pathlib
import uuid
from typing import Optional

from core.device.i_device import IDevice
from sqlmodel import Session

from core.test_session import (
    plan as core_plan,
    execution_plan,
    session as core_test_session,
)

from api.async_jobs import AsyncJobRunner
from api.config import settings
from api.models import (
    TestSession,
    ExecutionStep,
    SessionTestPlanPublic,
    BuildPublic,
    DeviceWithStatus,
)

logger = logging.getLogger(__name__)


def plan_execution(
    *,
    public_plan: SessionTestPlanPublic,
    xctestrun_path: pathlib.Path,
    xc_test_configuration_name: str,
) -> execution_plan.ExecutionPlan:
    """
    Plan the test session execution based on the public test plan, xctestrun path and test configuration.

    :param public_plan: The public test plan model
    :param xctestrun_path: The path to the xctestrun file
    :param xc_test_configuration_name: The test configuration to be used

    :return: The core execution plan model
    """
    core_session_test_plan = _parse_api_test_plan_to_core_test_plan(
        public_plan=public_plan,
        xctestrun_path=xctestrun_path.resolve().as_posix(),
        test_configuration=xc_test_configuration_name,
    )
    core_execution_plan = execution_plan.ExecutionPlan(test_plan=core_session_test_plan)
    core_execution_plan.plan()
    return core_execution_plan


def create_test_session(
    *,
    session: Session,
    public_plan: SessionTestPlanPublic,
    public_build: BuildPublic,
    public_device: DeviceWithStatus,
    xc_test_configuration_name: str,
    execution_steps: list[ExecutionStep] = None,
    session_id: Optional[uuid.UUID] = None,
) -> TestSession:
    """
    Create a new test session in the database.

    :param session: The database session
    :param public_plan: The public test plan model to create a snapshot of
    :param public_build: The public build model to create a snapshot of
    :param public_device: The public device model to create a snapshot of
    :param xc_test_configuration_name: The test configuration name to be used for execution
    :param execution_steps: The execution steps to be used for the test session
    :param session_id: The UUID of the test session
    :return: The database test session model
    """
    db_test_session = TestSession(
        id=session_id,
        plan_id=public_plan.id,
        plan_snapshot=public_plan.model_dump(mode="json"),
        build_id=public_build.id,
        build_snapshot=public_build.model_dump(mode="json"),
        device_id=public_device.id,
        device_snapshot=public_device.model_dump(mode="json"),
        execution_steps=execution_steps,
        xc_test_configuration_name=xc_test_configuration_name,
    )
    session.add(db_test_session)
    session.commit()
    session.refresh(db_test_session)
    return db_test_session


def construct_db_execution_step_models(
    *,
    test_session_id: uuid.UUID,
    core_execution_plan: execution_plan.ExecutionPlan,
) -> list[ExecutionStep]:
    """
    Constructs a list of database models for the execution steps using the test session ID and the core execution plan.
    """
    return [
        construct_db_execution_step_model(
            test_session_id=test_session_id,
            core_execution_step=core_execution_step,
        )
        for core_execution_step in core_execution_plan.execution_steps
    ]


def construct_db_execution_step_model(
    *,
    test_session_id: uuid.UUID,
    core_execution_step: execution_plan.ExecutionStep,
) -> ExecutionStep:
    """
    Constructs a database model for the execution step using the test session ID and the core execution step.
    """

    return ExecutionStep(
        recording_start_strategy=core_execution_step.recording_start_strategy,
        step_repetition=core_execution_step.step_repetition,
        plan_step_order=core_execution_step.plan_step_order,
        metrics=core_execution_step.metrics,
        session_id=test_session_id,
        test_cases=[
            test_case.xctest_id for test_case in core_execution_step.test_cases
        ],
        end_on_failure=core_execution_step.end_on_failure,
        test_target_name=core_execution_step.test_target.BlueprintName,
        plan_repetition=core_execution_step.plan_repetition,
        reinstall_app=core_execution_step.reinstall_app,
    )


def start_test_session(
    *,
    session: Session,
    i_device: IDevice,
    db_test_session: TestSession,
    job_runner: AsyncJobRunner,
    core_execution_plan: execution_plan.ExecutionPlan,
):
    """
    Start the test session in the background by adding the job to the job runner.
    """
    job_runner.add_job(
        func=_start_test_session_job,
        kwargs={
            "session": session,
            "db_test_session": db_test_session,
            "device": i_device,
            "core_execution_plan": core_execution_plan,
        },
        job_id=db_test_session.id.hex,
    )


def get_test_session_dir_path(*, test_session_id: uuid.UUID) -> pathlib.Path:
    """
    Return the path to the directory where the test session data is stored.
    """
    return settings.TEST_SESSIONS_DIR_PATH / test_session_id.hex


async def _start_test_session_job(
    *,
    session: Session,
    db_test_session: TestSession,
    device: IDevice,
    core_execution_plan: execution_plan.ExecutionPlan,
):
    """
    Execute the test session and update the status of the test session in the database based on the result.
    """
    db_test_session.status = "running"
    session.add(db_test_session)
    session.commit()

    try:
        output_dir = get_test_session_dir_path(test_session_id=db_test_session.id)
        output_dir.mkdir(exist_ok=True)

        test_session = core_test_session.Session(
            session_id=db_test_session.id,
            device=device,
            execution_plan=core_execution_plan,
            output_dir=output_dir.resolve().as_posix(),
        )
        await test_session.run()

        db_test_session.status = "completed"
        session.add(db_test_session)
        session.commit()
    except Exception as e:
        logger.exception(
            f"Error running test session '{db_test_session.id}'", exc_info=e
        )
        db_test_session.status = "failed"
        session.add(db_test_session)
        session.commit()


def _parse_api_test_plan_to_core_test_plan(
    *,
    public_plan: SessionTestPlanPublic,
    xctestrun_path: str,
    test_configuration: str,
) -> core_plan.SessionTestPlan:
    """
    Parse the public test plan model to the core test plan model.

    This can be used to validate the test plan against the requirements of the core test plan model.

    :param public_plan: The public test plan model
    :param xctestrun_path: The path to the xctestrun file. Not required if just validating the test plan
    :param test_configuration: The test configuration to be used. Not required if just validating the test plan

    :raises ValidationError:

    :return: The core test plan model
    """
    return core_plan.SessionTestPlan(
        name=public_plan.name,
        recording_start_strategy=public_plan.recording_start_strategy,
        reinstall_app=public_plan.reinstall_app,
        end_on_failure=public_plan.end_on_failure,
        repetitions=public_plan.repetitions,
        repetition_strategy=public_plan.repetition_strategy,
        metrics=public_plan.metrics,
        xctestrun_config=core_plan.XctestrunConfig(
            path=xctestrun_path,
            test_configuration=test_configuration,
        ),
        steps=[
            core_plan.PlanStep(
                name=step.name,
                order=step.order,
                recording_start_strategy=step.recording_start_strategy,
                reinstall_app=step.reinstall_app,
                metrics=step.metrics,
                repetitions=step.repetitions,
                test_cases=[
                    core_plan.StepTestCase(
                        xctest_id=case,
                    )
                    for case in step.test_cases
                ],
            )
            for step in public_plan.steps
        ],
    )


def generate_session_id() -> uuid.UUID:
    """
    Generate a new UUID for a test session.
    """
    return uuid.uuid4()

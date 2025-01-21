import uuid

from core.device.i_device_manager import IDeviceManager
from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from api.custom_responses import SSEStreamingResponse
from api.depends import SessionDep, AsyncJobRunnerDep, DeviceManagerDep
from api.models import (
    TestSessionCreate,
    TestSessionPublic,
    SessionTestPlanPublic,
    BuildPublic,
    DeviceWithStatus,
)
from api.services import (
    project_service,
    api_test_plan_service,
    device_service,
    api_test_session_service,
)

router = APIRouter(prefix="/test-sessions", tags=["testSession"])


@router.get("/")
async def list_test_sessions(*, session: SessionDep) -> list[TestSessionPublic]:
    """
    List all test sessions.
    """
    return api_test_session_service.list_test_sessions(session=session)


@router.post("/")
async def start_test_session(
    *,
    session: SessionDep,
    job_runner: AsyncJobRunnerDep,
    device_manager: DeviceManagerDep,
    session_create: TestSessionCreate,
) -> TestSessionPublic:
    """
    Create and start new test session.
    """
    public_build, public_plan, public_device = _validate_test_session_input(
        session=session,
        device_manager=device_manager,
        session_create=session_create,
    )

    core_execution_plan = api_test_session_service.plan_execution(
        public_plan=public_plan,
        xctestrun_path=public_build.xctestrun.path,
        xc_test_configuration_name=session_create.xc_test_configuration_name,
    )

    session_id = api_test_session_service.generate_session_id()

    execution_step_models = api_test_session_service.construct_db_execution_step_models(
        test_session_id=session_id,
        core_execution_plan=core_execution_plan,
    )

    db_test_session = api_test_session_service.create_test_session(
        session=session,
        public_plan=public_plan,
        public_build=public_build,
        public_device=public_device,
        execution_steps=execution_step_models,
        session_id=session_id,
        xc_test_configuration_name=session_create.xc_test_configuration_name,
    )

    api_test_session_service.start_test_session(
        job_runner=job_runner,
        test_session_id=session_id,
        core_execution_plan=core_execution_plan,
        i_device=device_manager.get_device(public_device.id),
    )

    return db_test_session


@router.get("/{test_session_id}")
async def read_test_session(
    *, session: SessionDep, test_session_id: uuid.UUID
) -> TestSessionPublic:
    """
    Get the details of a test session.
    """
    db_test_session = api_test_session_service.read_test_session(
        session=session, test_session_id=test_session_id
    )
    if db_test_session is None:
        raise HTTPException(status_code=404, detail="Test session not found")

    return db_test_session


@router.post("/{test_session_id}/cancel")
async def cancel_test_session(
    *, session: SessionDep, job_runner: AsyncJobRunnerDep, test_session_id: uuid.UUID
):
    """
    Cancels a running test session.
    """
    pass


@router.get("/{test_session_id}/execution-step-stream")
async def stream_execution_step_updates(
    *, session: SessionDep, test_session_id: uuid.UUID
) -> SSEStreamingResponse:
    """
    Stream updates of the execution steps of a test session. Can return any execution step when it is updated.
    """
    pass


@router.post("/{test_session_id}/process-trace-results")
async def export_test_session_results(
    *, session: SessionDep, test_session_id: uuid.UUID
):
    """
    Start processing the trace results of a test session.
    """
    pass


def _validate_test_session_input(
    *,
    session: Session,
    device_manager: IDeviceManager,
    session_create: TestSessionCreate,
) -> tuple[BuildPublic, SessionTestPlanPublic, DeviceWithStatus]:
    """
    Validate the input for the test session creation and return the build, plan and device.

    :param session: The database session
    :param device_manager: The device manager
    :param session_create: The test session creation model

    :raises HTTPException: If the input is invalid or specific conditions are not met

    :return: The build, plan and device
    """
    db_build = project_service.read_build(
        session=session, build_id=session_create.build_id
    )
    if db_build is None:
        raise HTTPException(status_code=400, detail="Invalid build id")

    db_plan = api_test_plan_service.read_test_plan(
        session=session, test_plan_id=session_create.plan_id
    )
    if db_plan is None:
        raise HTTPException(status_code=400, detail="Invalid plan id")

    if db_plan.project_id != db_build.project_id:
        # We're not validating if the test plan is part of the project. There could be the situation where there the
        # test plan and build that was created before the test plan was removed from the project. This would still
        # allow the user to run the tests with the existing build artefacts.
        raise HTTPException(
            status_code=400, detail="Plan and build must belong to the same project"
        )

    if db_plan.xc_test_plan_name != db_build.test_plan:
        raise HTTPException(
            status_code=400, detail="Plan and build must belong to the same test plan"
        )

    if db_build.status != "success":
        raise HTTPException(status_code=400, detail="Build must be completed")

    if (
        session_create.xc_test_configuration_name
        not in db_build.xctestrun.test_configurations
    ):
        raise HTTPException(status_code=400, detail="Invalid test configuration name")

    if db_build.xctestrun.path is None or db_build.xctestrun.path.exists() is False:
        raise HTTPException(
            status_code=400,
            detail="Xctestrun file not found. Try rebuilding the project",
        )

    device_with_status = device_service.get_device_by_id(
        session=session, device_id=db_build.device_id, device_manager=device_manager
    )
    if device_with_status is None or not device_with_status.connected:
        raise HTTPException(status_code=400, detail="Device not connected")

    if device_with_status.status.tunnel_connected is False:
        raise HTTPException(
            status_code=400, detail="No tunnel connection to the device"
        )

    public_build = BuildPublic.model_validate(db_build)
    public_plan = SessionTestPlanPublic.model_validate(db_plan)

    return public_build, public_plan, device_with_status

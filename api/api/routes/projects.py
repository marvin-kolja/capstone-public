import uuid

from core.xc.app_builder import AppBuilder
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.custom_responses import (
    SSEStreamingResponse,
    build_common_http_exception_responses,
)
from api.depends import SessionDep, DeviceManagerDep, AsyncJobRunnerDep
from api.services import project_service, device_service
from api.models import (
    XcProjectPublic,
    XcProjectCreate,
    BuildPublic,
    StartBuildRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "/",
    responses=build_common_http_exception_responses([500]),
)
async def list_projects(*, session: SessionDep) -> list[XcProjectPublic]:
    """
    List all projects.
    """
    return project_service.list_projects(session=session)


@router.post(
    "/",
    responses=build_common_http_exception_responses([400, 422, 500]),
)
async def add_project(
    *, session: SessionDep, project: XcProjectCreate
) -> XcProjectPublic:
    """
    Add a new project.
    """
    try:
        xc_project_interface = project_service.get_core_xc_project(path=project.path)
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail="Invalid project path") from e

    try:
        return await project_service.add_project(
            session=session, xc_project_interface=xc_project_interface
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add project") from e


@router.get(
    "/{project_id}",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def read_project(
    *, session: SessionDep, project_id: uuid.UUID
) -> XcProjectPublic:
    """
    Get the details of a project.
    """
    project = project_service.read_project(session=session, project_id=project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post(
    "/{project_id}/refresh",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def refresh_project(
    *, session: SessionDep, project_id: uuid.UUID
) -> XcProjectPublic:
    """
    Refreshes the data of a project.
    """
    db_project = project_service.read_project(session=session, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        xc_project_interface = project_service.get_core_xc_project(path=db_project.path)
    except ValueError:
        # If the path isn't valid anymore, we can't refresh the project. Thus, we simply return the project as is.
        # TODO: We could also mark the project as invalid and allow the user to fix the path.
        return XcProjectPublic.model_validate(db_project)

    return await project_service.refresh_project(
        session=session,
        db_project=db_project,
        xc_project_interface=xc_project_interface,
    )


@router.get(
    "/{project_id}/builds",
    responses=build_common_http_exception_responses([422, 500]),
)
async def list_builds(
    *, session: SessionDep, project_id: uuid.UUID
) -> list[BuildPublic]:
    """
    List builds that belong to a project.
    """
    return project_service.list_builds(session=session, project_id=project_id)


@router.post(
    "/{project_id}/builds",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def start_build(
    *,
    session: SessionDep,
    device_manager: DeviceManagerDep,
    job_runner: AsyncJobRunnerDep,
    project_id: uuid.UUID,
    build_request: StartBuildRequest,
) -> BuildPublic:
    """
    Start a new build for a project.
    """
    db_project = project_service.read_project(session=session, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project_service.validate_build_request(
        db_project=db_project, build_request=build_request
    )

    try:
        xc_project = project_service.get_core_xc_project(path=db_project.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid project path") from e

    device = device_service.get_device_by_id(
        session=session,
        device_id=build_request.device_id,
        device_manager=device_manager,
    )
    if device is None or not device.connected:
        raise HTTPException(status_code=404, detail="Device not found")

    db_build = project_service.get_unique_build(
        session=session,
        project_id=project_id,
        build_request=build_request,
    ) or project_service.create_build(
        session=session,
        project_id=project_id,
        build_request=build_request,
    )

    job_id = project_service.get_build_job_id(
        db_build=db_build,
    )
    if job_runner.job_exists(job_id):
        raise HTTPException(status_code=400, detail="Build already in progress")

    project_service.start_build(
        session=session,
        db_build=db_build,
        app_builder=AppBuilder(xc_project=xc_project),
        job_runner=job_runner,
        job_id=job_id,
    )

    return db_build


@router.get(
    "/{project_id}/builds/{build_id}",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def read_build(
    *, session: SessionDep, project_id: uuid.UUID, build_id: uuid.UUID
) -> BuildPublic:
    """
    Get the details of a build.
    """
    db_build = project_service.read_build(
        session=session, project_id=project_id, build_id=build_id
    )
    if db_build is None:
        raise HTTPException(status_code=404, detail="Build not found")
    return db_build


@router.get(
    "/{project_id}/builds/{build_id}/update-stream",
    response_class=SSEStreamingResponse,
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def stream_build_updates(
    *, session: SessionDep, project_id: uuid.UUID, build_id: uuid.UUID, request: Request
) -> StreamingResponse:
    """
    Stream build status updates.
    """
    db_build = project_service.read_build(
        session=session, project_id=project_id, build_id=build_id
    )
    if db_build is None:
        raise HTTPException(status_code=404, detail="Build not found")

    # noinspection PyStatementEffect
    db_build.xctestrun
    # The DB session is closed before the async generator is called. Because of this SQLAlchemy lazy loading cannot work
    # as the `db_build` is detached from the session when used in the async generator. This is a workaround to ensure
    # the `xctestrun` is loaded. Read more on this here: https://docs.sqlalchemy.org/en/20/errors.html#error-bhk3

    return StreamingResponse(
        project_service.listen_to_build_updates(db_build=db_build, request=request),
        media_type="text/event-stream",
    )


@router.get(
    "/{project_id}/builds/{build_id}/available-tests",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def list_available_tests(
    *,
    session: SessionDep,
    device_manager: DeviceManagerDep,
    project_id: uuid.UUID,
    build_id: uuid.UUID,
) -> list[str]:
    """
    This will list the available tests for a builds' xctestrun file. Provided the build is finished, the xctestrun file
    is available and the device the build war run on is connected. If any of these conditions are not met, an error will
    be raised.
    """
    db_build = project_service.read_build(
        session=session, project_id=project_id, build_id=build_id
    )
    if db_build is None:
        raise HTTPException(status_code=404, detail="Build not found")

    if db_build.xctestrun is None or db_build.status != "success":
        raise HTTPException(status_code=400, detail="Build is not finished")

    device = device_service.get_device_by_id(
        session=session, device_id=db_build.device_id, device_manager=device_manager
    )

    if device is None or not device.connected:
        raise HTTPException(status_code=400, detail="Device is not connected")

    xc_test_cases = await project_service.list_available_tests(db_build=db_build)

    db_build.xc_test_cases = xc_test_cases
    session.add(db_build)
    session.commit()

    return xc_test_cases

import uuid

from fastapi import APIRouter, HTTPException

from api.depends import SessionDep
from api.models import XcProjectPublic, XcProjectCreate
from api.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
async def list_projects(*, session: SessionDep) -> list[XcProjectPublic]:
    """
    List all projects.
    """
    return project_service.list_projects(session=session)


@router.post("/")
async def add_project(
    *, session: SessionDep, project: XcProjectCreate
) -> XcProjectPublic:
    """
    Add a new project.
    """
    try:
        xc_project_interface = project_service.get_core_xc_project(path=project.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid project path") from e

    try:
        return await project_service.add_project(
            session=session, xc_project_interface=xc_project_interface
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add project") from e


@router.get("/{project_id}")
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


@router.post("/{project_id}/refresh")
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


@router.get("/{project_id}/builds")
async def list_builds(project_id: str):
    """
    List builds that belong to a project.
    """
    pass


@router.post("/{project_id}/builds")
async def start_build(project_id: str):
    """
    Start a new build for a project.
    """
    pass


@router.get("/{project_id}/builds/{build_id}")
async def read_build(project_id: str, build_id: str):
    """
    Get the details of a build.
    """


@router.get("/{project_id}/builds/{build_id}/update-stream")
async def stream_build_updates(project_id: str, build_id: str):
    """
    Stream build status updates.
    """
    pass

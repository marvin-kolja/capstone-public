import uuid

from fastapi import APIRouter

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
    return await project_service.add_project(session=session, project=project)


@router.get("/{project_id}")
async def read_project(
    *, session: SessionDep, project_id: uuid.UUID
) -> XcProjectPublic:
    """
    Get the details of a project.
    """
    return project_service.read_project(session=session, project_id=project_id)


@router.post("/{project_id}/refresh")
async def refresh_project(
    *, session: SessionDep, project_id: uuid.UUID
) -> XcProjectPublic:
    """
    Refreshes the data of a project.
    """
    return await project_service.refresh_project(session=session, project_id=project_id)


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

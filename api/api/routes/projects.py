from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/")
async def list_projects():
    """
    List all projects.
    """
    pass


@router.post("/")
async def add_project():
    """
    Add a new project.
    """
    pass


@router.get("/{project_id}")
async def read_project(project_id: int):
    """
    Get the details of a project.
    """
    pass


@router.post("/{project_id}/refresh")
async def refresh_project(project_id: int):
    """
    Refreshes the data of a project.
    """
    pass


@router.get("/{project_id}/builds")
async def list_builds(project_id: int):
    """
    List builds that belong to a project.
    """
    pass


@router.post("/{project_id}/builds")
async def start_build(project_id: int):
    """
    Start a new build for a project.
    """
    pass


@router.get("/{project_id}/builds/{build_id}")
async def read_build(project_id: int, build_id: int):
    """
    Get the details of a build.
    """


@router.get("/{project_id}/builds/{build_id}/update-stream")
async def stream_build_updates(project_id: int, build_id: int):
    """
    Stream build status updates.
    """
    pass

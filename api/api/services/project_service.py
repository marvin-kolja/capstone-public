import uuid

from sqlmodel import Session

from api.models import XcProjectPublic, XcProjectCreate


def list_projects(*, session: Session) -> list[XcProjectPublic]:
    # 1. Get all projects from DB
    raise NotImplementedError


def add_project(*, session: Session, project: XcProjectCreate) -> XcProjectPublic:
    # 1. Validate path to project
    # 2. Validate project name
    # 3. List configurations, schemes, targets
    # 4. List xc test plans for each schema
    # 5. Store information in DB
    raise NotImplementedError


def read_project(*, session: Session, project_id: uuid.UUID) -> XcProjectPublic:
    # 1. Get project from DB
    raise NotImplementedError


def refresh_project(*, session: Session, project_id: uuid.UUID) -> XcProjectPublic:
    # 1. Get project from DB
    # 2. List configurations, schemes, targets
    # 3. List xc test plans for each schema
    # 4. Update information in DB
    #
    # Is very similar to add_project, so we can reuse the code
    raise NotImplementedError

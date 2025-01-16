import uuid

from fastapi import HTTPException
from sqlmodel import Session, select

from api.models import XcProjectPublic, XcProjectCreate, XcProject


def list_projects(*, session: Session) -> list[XcProjectPublic]:
    db_projects = session.exec(select(XcProject)).all()
    return [XcProjectPublic.model_validate(project) for project in db_projects]


def add_project(*, session: Session, project: XcProjectCreate) -> XcProjectPublic:
    # 1. Validate path to project
    # 2. Validate project name
    # 3. List configurations, schemes, targets
    # 4. List xc test plans for each schema
    # 5. Store information in DB
    raise NotImplementedError


def read_project(*, session: Session, project_id: uuid.UUID) -> XcProjectPublic:
    db_project = session.exec(
        select(XcProject).where(XcProject.id == project_id)
    ).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return XcProjectPublic.model_validate(db_project)


def refresh_project(*, session: Session, project_id: uuid.UUID) -> XcProjectPublic:
    # 1. Get project from DB
    # 2. List configurations, schemes, targets
    # 3. List xc test plans for each schema
    # 4. Update information in DB
    #
    # Is very similar to add_project, so we can reuse the code
    raise NotImplementedError

import uuid

from fastapi import HTTPException
from sqlmodel import Session, select

from api.models import (
    XcProjectPublic,
    XcProjectCreate,
    XcProject,
    XcProjectConfiguration,
    XcProjectTarget,
    XcProjectScheme,
    XcProjectTestPlan,
)
from core.xc import xc_project as core_xc_project


def list_projects(*, session: Session) -> list[XcProjectPublic]:
    db_projects = session.exec(select(XcProject)).all()
    return [XcProjectPublic.model_validate(project) for project in db_projects]


async def add_project(*, session: Session, project: XcProjectCreate) -> XcProjectPublic:
    try:
        core_project = core_xc_project.XcProject(project.path.resolve().as_posix())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path to project")

    project_details = await core_project.list()

    db_project = XcProject(name=project_details.name, path=project.path)
    session.add(db_project)

    for configuration in project_details.configurations:
        db_configuration = XcProjectConfiguration(
            name=configuration,
            project_id=db_project.id,
        )
        session.add(db_configuration)
    for target in project_details.targets:
        db_target = XcProjectTarget(
            name=target,
            project_id=db_project.id,
        )
        session.add(db_target)
    for scheme in project_details.schemes:
        db_scheme = XcProjectScheme(
            name=scheme,
            project_id=db_project.id,
        )
        session.add(db_scheme)
        for xc_test_plan in await core_project.xcode_test_plans(scheme=scheme):
            db_test_plan = XcProjectTestPlan(
                name=xc_test_plan,
                scheme_id=db_scheme.id,
                project_id=db_project.id,
            )
            session.add(db_test_plan)

    session.commit()
    session.refresh(db_project)

    return XcProjectPublic.model_validate(db_project)


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
    # 3. List xc test plans for each scheme
    # 4. Update information in DB
    #
    # Is very similar to add_project, so we can reuse the code
    raise NotImplementedError

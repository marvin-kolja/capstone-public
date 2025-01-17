import uuid
from typing import Optional, TypeVar

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

    db_project = XcProject(
        name="", path=project.path
    )  # Uses a blank name for now as it will be updated in sync_db_project
    await sync_db_project(
        session=session, db_project=db_project, xc_project=core_project
    )
    session.add(db_project)

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


async def refresh_project(
    *, session: Session, project_id: uuid.UUID
) -> XcProjectPublic:
    # 1. Get project from DB
    # 2. List configurations, schemes, targets
    # 3. List xc test plans for each scheme
    # 4. Update information in DB
    #
    # Is very similar to add_project, so we can reuse the code
    db_project = session.exec(
        select(XcProject).where(XcProject.id == project_id)
    ).first()

    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        core_project = core_xc_project.XcProject(db_project.path.resolve().as_posix())
    except ValueError:
        # If the path isn't valid anymore, we can't refresh the project. Thus, we simply return the project as is.
        # TODO: We could also mark the project as invalid and allow the user to fix the path.
        return XcProjectPublic.model_validate(db_project)

    await sync_db_project(
        session=session, db_project=db_project, xc_project=core_project
    )

    session.commit()
    session.refresh(db_project)

    return XcProjectPublic.model_validate(db_project)


_ProjectResource = TypeVar(
    "_ProjectResource",
    XcProjectConfiguration,
    XcProjectTarget,
    XcProjectScheme,
    XcProjectTestPlan,
)


def sync_project_resources(
    *,
    session: Session,
    db_items: list[_ProjectResource],
    new_item_names: list[str],
    project_id: uuid.UUID,
    model_class: type[_ProjectResource],
    additional_fields: Optional[dict] = None,
) -> list[_ProjectResource]:
    """
    Synchronizes the resources of a project with the new items.

    **NOTE: This does not flush or commit the changes done to the DB!**

    This is used to synchronize one of configurations, targets, and schemes of a project with the new items that are
    retrieved using :meth:`core.xc.xc_project.XcProject.list`. This can also be used for xc test plans of a scheme
    retrieved using :meth:`core.xc.xc_project.XcProject.xcode_test_plans`.

    New items are strings that represent the names of the items (`new_item_names`). The items that are currently in the
    database are represented by the `db_items`. The project_id is the ID of the project that the items belong to.

    Names of items that are in the database but not in the new items are removed. New items that are not in the database
    are added.

    :param session: The database session
    :param db_items: The items that are currently in the database
    :param new_item_names: The new items that should be in the database
    :param project_id: The ID of the project that the items belong to
    :param model_class: The model class to use for new items
    :param additional_fields: Additional fields that should be set for the new items

    :return: The new list of db items
    """
    existing_item_names = [item.name for item in db_items]
    result = []

    for db_item in db_items:
        # Remove items that are not in the new items anymore
        if db_item.name not in new_item_names:
            session.delete(db_item)
        else:
            # Still exists, add to the result list
            result.append(db_item)  # Add to the new list

    for new_item_name in new_item_names:
        # Add new items
        if new_item_name not in existing_item_names:
            db_item = model_class(
                name=new_item_name,
                project_id=project_id,
                **(additional_fields if additional_fields else {}),
            )
            session.add(db_item)
            result.append(db_item)  # Add to the new list

    return result


async def sync_db_project(
    *,
    session: Session,
    db_project: XcProject,
    xc_project: core_xc_project.XcProject,
):
    """
    Synchronizes all resources of a project with the new items.

    **NOTE: This does not flush or commit the changes done to the DB!**

    This is used to synchronize the project name, configurations, targets, schemes, and xc test plans of each scheme
    of a project. Those are retrieved using :meth:`core.xc.xc_project.XcProject.list`.
    Xc test plans for each scheme are retrieved using :meth:`core.xc.xc_project.XcProject.xcode_test_plans`.

    :param session: The database session
    :param db_project:  The project that is currently in the database
    :param xc_project: The core project instance that is used to get the new items
    """
    project_details = await xc_project.list()

    if project_details.name != db_project.name:
        db_project.name = project_details.name

    sync_project_resources(
        session=session,
        db_items=db_project.configurations,
        new_item_names=project_details.configurations,
        project_id=db_project.id,
        model_class=XcProjectConfiguration,
    )
    sync_project_resources(
        session=session,
        db_items=db_project.targets,
        new_item_names=project_details.targets,
        project_id=db_project.id,
        model_class=XcProjectTarget,
    )
    db_schemes = sync_project_resources(
        session=session,
        db_items=db_project.schemes,
        new_item_names=project_details.schemes,
        project_id=db_project.id,
        model_class=XcProjectScheme,
    )

    for db_scheme in db_schemes:
        xc_test_plans = await xc_project.xcode_test_plans(scheme=db_scheme.name)

        sync_project_resources(
            session=session,
            db_items=db_scheme.xc_test_plans,
            new_item_names=xc_test_plans,
            project_id=db_project.id,
            model_class=XcProjectTestPlan,
            additional_fields={"scheme_id": db_scheme.id},
        )

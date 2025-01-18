import logging
import pathlib
import uuid
from typing import Optional, TypeVar

from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from api.models import (
    XcProjectPublic,
    XcProject,
    XcProjectConfiguration,
    XcProjectTarget,
    XcProjectScheme,
    XcProjectTestPlan,
    Build,
    BuildPublic,
)
from core.xc import xc_project as core_xc_project

logger = logging.getLogger(__name__)


def list_projects(*, session: Session) -> list[XcProjectPublic]:
    db_projects = session.exec(select(XcProject)).all()
    return [XcProjectPublic.model_validate(project) for project in db_projects]


def get_core_xc_project(*, path: pathlib.Path) -> core_xc_project.XcProject:
    """
    Get the core xc project instance using the path to the project.

    :raises ValueError: If the path to the project is invalid
    """
    return core_xc_project.XcProject(path.resolve().as_posix())


async def add_project(
    *, session: Session, xc_project_interface: core_xc_project.XcProject
) -> XcProjectPublic:
    """
    Add a new project to the database after it was validated and information was retrieved from the project.

    :raises core.subprocess.ProcessException: If commands to retrieve additional infos fails
    :raises ValidationError: If validation of data fails
    """
    db_project = XcProject(
        name="", path=pathlib.Path(xc_project_interface.path_to_project)
    )  # Uses a blank name for now as it will be updated in sync_db_project
    await sync_db_project(
        session=session, db_project=db_project, xc_project=xc_project_interface
    )
    session.add(db_project)

    session.commit()
    session.refresh(db_project)

    return XcProjectPublic.model_validate(db_project)


def read_project(*, session: Session, project_id: uuid.UUID) -> Optional[XcProject]:
    db_project = session.exec(
        select(XcProject).where(XcProject.id == project_id)
    ).first()
    if db_project is None:
        return None
    return db_project


async def refresh_project(
    *,
    session: Session,
    db_project: XcProject,
    xc_project_interface: core_xc_project.XcProject,
) -> XcProjectPublic:
    await sync_db_project(
        session=session, db_project=db_project, xc_project=xc_project_interface
    )

    session.commit()
    session.refresh(db_project)

    return XcProjectPublic.model_validate(db_project)


def list_builds(*, session: Session, project_id: uuid.UUID) -> list[BuildPublic]:
    db_builds = session.exec(select(Build).where(Build.project_id == project_id)).all()
    logger.debug(f"Found {len(db_builds)} builds for project '{project_id}'")
    return [BuildPublic.model_validate(build) for build in db_builds]


def read_build(
    *, session: Session, project_id: uuid.UUID, build_id: uuid.UUID
) -> Optional[Build]:
    try:
        db_build = session.exec(
            select(Build)
            .where(Build.id == build_id)
            .where(Build.project_id == project_id)
        ).one()
        logger.debug(f"Found build '{build_id}' for project '{project_id}'")
        return db_build
    except NoResultFound:
        logger.debug(f"Build '{build_id}' not found for project '{project_id}'")
        return None


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

    :raises core.subprocess.ProcessException: If commands to retrieve additional infos fails
    :raises ValidationError: If the output of the command cannot be parsed correctly
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

import logging
import pathlib
import uuid
from typing import Optional, TypeVar, AsyncGenerator

from core.xc.app_builder import AppBuilder
from core.xc.commands.xcodebuild_command import IOSDestination
from core.xc.xctest import Xctest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from api.async_jobs import AsyncJobRunner
from api.config import settings
from api.db import async_session_maker
from api.models import (
    XcProjectPublic,
    XcProject,
    XcProjectConfiguration,
    XcProjectTarget,
    XcProjectScheme,
    XcProjectTestPlan,
    Build,
    BuildPublic,
    StartBuildRequest,
    Xctestrun,
)
from core.xc import xc_project as core_xc_project

from api.services.orm_update_listener import ModelUpdateListener

logger = logging.getLogger(__name__)


async def list_projects(*, session: AsyncSession) -> list[XcProjectPublic]:
    db_projects = (await session.execute(select(XcProject))).scalars().all()
    return [XcProjectPublic.model_validate(project) for project in db_projects]


def get_core_xc_project(*, path: pathlib.Path) -> core_xc_project.XcProject:
    """
    Get the core xc project instance using the path to the project.

    :raises ValueError: If the path to the project is invalid
    """
    return core_xc_project.XcProject(path.resolve().as_posix())


async def add_project(
    *, session: AsyncSession, xc_project_interface: core_xc_project.XcProject
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

    await session.commit()
    await session.refresh(db_project)

    return XcProjectPublic.model_validate(db_project)


async def read_project(
    *, session: AsyncSession, project_id: uuid.UUID
) -> Optional[XcProject]:
    statement = select(XcProject).where(XcProject.id == project_id)
    db_project = (await session.execute(statement)).scalar_one_or_none()
    if db_project is None:
        return None
    return db_project


async def refresh_project(
    *,
    session: AsyncSession,
    db_project: XcProject,
    xc_project_interface: core_xc_project.XcProject,
) -> XcProjectPublic:
    await sync_db_project(
        session=session, db_project=db_project, xc_project=xc_project_interface
    )

    await session.commit()
    await session.refresh(db_project)

    return XcProjectPublic.model_validate(db_project)


async def list_builds(
    *, session: AsyncSession, project_id: uuid.UUID
) -> list[BuildPublic]:
    statement = select(Build).where(Build.project_id == project_id)
    db_builds = (await session.execute(statement)).scalars().all()
    logger.debug(f"Found {len(db_builds)} builds for project '{project_id}'")
    return [BuildPublic.model_validate(build) for build in db_builds]


async def read_build(
    *,
    session: AsyncSession,
    build_id: uuid.UUID,
    project_id: Optional[uuid.UUID] = None,
) -> Optional[Build]:
    try:
        statement = select(Build).where(Build.id == build_id)
        if project_id:
            statement = statement.where(Build.project_id == project_id)

        db_build = (await session.execute(statement)).scalar_one_or_none()
        logger.debug(f"Found build '{build_id}'")
        return db_build
    except NoResultFound:
        logger.debug(f"Build '{build_id}' not found")
        return None


def validate_build_request(
    *,
    db_project: XcProject,
    build_request: StartBuildRequest,
):
    """
    Makes sure that the build request is valid for the project. Checks scheme, configuration, and test plan.

    :raises RequestValidationError: If the build request is invalid
    """
    if build_request.scheme not in [scheme.name for scheme in db_project.schemes]:
        raise RequestValidationError(
            errors=[
                {
                    "loc": ["body", "scheme"],
                    "msg": "Invalid scheme",
                    "type": "value_error",
                }
            ]
        )

    if build_request.configuration not in [
        configuration.name for configuration in db_project.configurations
    ]:
        raise RequestValidationError(
            errors=[
                {
                    "loc": ["body", "configuration"],
                    "msg": "Invalid configuration",
                    "type": "value_error",
                }
            ]
        )

    scheme = next(
        scheme for scheme in db_project.schemes if scheme.name == build_request.scheme
    )

    if build_request.test_plan not in [
        xc_test_plan.name for xc_test_plan in scheme.xc_test_plans
    ]:
        raise RequestValidationError(
            errors=[
                {
                    "loc": ["body", "test_plan"],
                    "msg": "Invalid test plan",
                    "type": "value_error",
                }
            ]
        )


def get_build_job_id(*, db_build: Build) -> str:
    """
    Creates an id from the project id and the build request data.

    The values are joined with a dash: `project_id-device_id-scheme-configuration-test_plan`.

    :param db_build: The build for which the job id should be created
    :return: The job id as string
    """
    return "-".join(
        [
            db_build.project_id.hex,
            db_build.device_id,
            db_build.scheme,
            db_build.configuration,
            db_build.test_plan,
        ]
    )


async def get_unique_build(
    *,
    session: AsyncSession,
    project_id: uuid.UUID,
    build_request: StartBuildRequest,
) -> Optional[Build]:
    try:
        statement = (
            select(Build)
            .where(Build.project_id == project_id)
            .where(Build.device_id == build_request.device_id)
            .where(Build.scheme == build_request.scheme)
            .where(Build.configuration == build_request.configuration)
            .where(Build.test_plan == build_request.test_plan)
            .options(selectinload(Build.xctestrun))
        )

        return (await session.execute(statement)).scalar_one()
    except NoResultFound:
        return None


async def create_build(
    *,
    session: AsyncSession,
    project_id: uuid.UUID,
    build_request: StartBuildRequest,
) -> Build:
    """
    Create a new build in the database.
    """
    db_build = Build(
        project_id=project_id,
        device_id=build_request.device_id,
        scheme=build_request.scheme,
        configuration=build_request.configuration,
        test_plan=build_request.test_plan,
    )
    session.add(db_build)
    await session.commit()
    await session.refresh(db_build)

    return db_build


async def start_build(
    *,
    session: AsyncSession,
    db_build: Build,
    job_runner: AsyncJobRunner,
    app_builder: AppBuilder,
    job_id: str,
):
    """
    Reset build status and xctestrun path and start the build job.
    """
    db_build.status = "pending"
    # Clear the test cases as they could change after a new builds
    db_build.xc_test_cases = None
    # Clear the xctestrun path as the new build will generate a new one
    if db_build.xctestrun:
        await session.delete(db_build.xctestrun)
    await session.commit()
    await session.refresh(db_build)

    job_runner.add_job(
        _build_project_job,
        kwargs={
            "app_builder": app_builder,
            "build_id": db_build.id,
            "output_dir": build_output_dir(db_build=db_build).resolve().as_posix(),
        },
        job_id=job_id,
    )


def build_output_dir(*, db_build: Build) -> pathlib.Path:
    """
    Get the output directory for the build relative to the base build directory defined in the settings.
    """
    return settings.BUILD_DIR_PATH / db_build.id.hex


async def _build_project_job(
    *,
    app_builder: AppBuilder,
    build_id: uuid.UUID,
    output_dir: str,
):
    print(async_session_maker)
    async with async_session_maker() as session:
        db_build = await read_build(session=session, build_id=build_id)

        logger.info(f"Starting build for project '{db_build.project_id}'")

        destination = IOSDestination(id=db_build.device_id)

        logger.debug(f"Setting build status to 'running' for build '{db_build.id}'")

        db_build.status = "running"
        session.add(db_build)
        await session.commit()

        logger.debug(f"Starting build for testing for project '{db_build.project_id}'")

        try:
            build_for_testing_result = await app_builder.build_for_testing(
                configuration=db_build.configuration,
                scheme=db_build.scheme,
                destination=destination,
                test_plan=db_build.test_plan,
                output_dir=output_dir,
                clean=True,  # Always clean the build directory
            )

            logger.debug(
                f"Build for testing for project '{db_build.project_id}' finished successfully"
            )

            logger.debug(
                f"Parsing xctestrun file '{build_for_testing_result.xctestrun_path}'"
            )
            xctestrun = Xctest.parse_xctestrun(build_for_testing_result.xctestrun_path)

            logger.debug(f"Creating xctestrun for build '{db_build.id}'")
            db_xctestrun = Xctestrun(
                path=pathlib.Path(build_for_testing_result.xctestrun_path),
                test_configurations=[
                    test_configuration.Name
                    for test_configuration in xctestrun.TestConfigurations
                ],
                build_id=db_build.id,
            )
            db_build.xctestrun = db_xctestrun
            session.add(db_build)
            await session.commit()

            requires_normal_build = False
            # Usually, the app that is tested is built when building for testing, as it is set as a Target Dependency in the
            # Build Phases of the Test Target. However, we don't know what the developer has done in the project, so we
            # check if the app exists in the derived data directory. If it doesn't, we perform another build.

            for test_configuration in xctestrun.TestConfigurations:
                for test_target in test_configuration.TestTargets:
                    if not pathlib.Path(test_target.app_path).exists():
                        requires_normal_build = True
                        break

            if requires_normal_build:
                logger.debug(
                    f"Normal build required for project '{db_build.project_id}', starting..."
                )
                await app_builder.build(
                    configuration=db_build.configuration,
                    scheme=db_build.scheme,
                    destination=destination,
                    output_dir=output_dir,
                    clean=False,  # Don't clean the build directory, as it was already cleaned in the build for testing step
                )

            logger.debug(
                f"Normal build for project '{db_build.project_id}' finished successfully"
            )

            db_build.status = "success"
            session.add(db_build)
            await session.commit()

            logger.info(
                f"Build for project '{db_build.project_id}' finished successfully"
            )
        except Exception as e:
            logger.error(
                f"Build for project '{db_build.project_id}' failed", exc_info=e
            )
            db_build.status = "failure"
            session.add(db_build)
            await session.commit()


async def listen_to_build_updates(
    *, db_build: Build, request: Request
) -> AsyncGenerator[str, None]:
    """
    An async generator that listens to updates of a build and yields the updated build.

    This is done until the build status is set to 'success' or 'failure', or the request is disconnected.
    """

    listener = ModelUpdateListener(
        db_instance=db_build,
        model_class=Build,
    )

    async for update in listener.listen():
        async with async_session_maker() as session:
            if update is None:
                if await request.is_disconnected():
                    logger.debug(f"Request disconnected, stopping listener")
                    listener.stop()
                continue

            if update.id != db_build.id:
                continue  # Skip updates for other builds

            build = await read_build(
                session=session, build_id=update.id, project_id=update.project_id
            )
            await session.refresh(build)  # Refresh the build to get the latest data

            yield "data: " + BuildPublic.model_validate(
                build
            ).model_dump_json() + "\n\n"

            if update.status == "success" or update.status == "failure":
                logger.debug(f"Build '{update.id}' finished, stopping listener")
                listener.stop()


async def list_available_tests(*, db_build: Build) -> list[str]:
    """
    Uses the xctestrun to execute a dry run of the tests on device to get the list of enabled tests.
    """
    list_result = await Xctest.list_tests(
        db_build.xctestrun.path.resolve().as_posix(),
        IOSDestination(id=db_build.device_id),
    )

    return list_result.enabledTests


_ProjectResource = TypeVar(
    "_ProjectResource",
    XcProjectConfiguration,
    XcProjectTarget,
    XcProjectScheme,
    XcProjectTestPlan,
)


async def sync_project_resources(
    *,
    session: AsyncSession,
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
            await session.delete(db_item)
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
    session: AsyncSession,
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

    await sync_project_resources(
        session=session,
        db_items=db_project.configurations,
        new_item_names=project_details.configurations,
        project_id=db_project.id,
        model_class=XcProjectConfiguration,
    )
    await sync_project_resources(
        session=session,
        db_items=db_project.targets,
        new_item_names=project_details.targets,
        project_id=db_project.id,
        model_class=XcProjectTarget,
    )
    db_schemes = await sync_project_resources(
        session=session,
        db_items=db_project.schemes,
        new_item_names=project_details.schemes,
        project_id=db_project.id,
        model_class=XcProjectScheme,
    )

    for db_scheme in db_schemes:
        xc_test_plans = await xc_project.xcode_test_plans(scheme=db_scheme.name)

        await sync_project_resources(
            session=session,
            db_items=db_scheme.xc_test_plans,
            new_item_names=xc_test_plans,
            project_id=db_project.id,
            model_class=XcProjectTestPlan,
            additional_fields={"scheme_id": db_scheme.id},
        )


async def project_has_xc_test_plan(
    *, session: AsyncSession, project_id: uuid.UUID, xc_test_plan: str
) -> bool:
    """
    Check if a project has a specific xc test plan.
    """
    statement = (
        select(XcProjectTestPlan)
        .join(XcProject)
        .where(XcProject.id == project_id)
        .where(XcProjectTestPlan.name == xc_test_plan)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none() is not None

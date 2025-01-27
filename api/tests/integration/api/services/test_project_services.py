import asyncio
import pathlib
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from core.xc.app_builder import AppBuilder
from fastapi import Request
from sqlmodel import select

from api.async_jobs import AsyncJobRunner
from api.models import Build, StartBuildRequest, BuildPublic
from api.services.project_service import (
    get_unique_build,
    create_build,
    start_build,
    _build_project_job,
    listen_to_build_updates,
)


def test_unique_build(db, new_db_fake_build):
    """
    GIVEN: A build in the database

    WHEN: Trying to get the build

    THEN: The build should be returned
    """
    build_request = StartBuildRequest(
        scheme="Release",
        test_plan="RP Swift",
        device_id=new_db_fake_build.device_id,
        configuration="Release",
    )

    db_build = get_unique_build(
        session=db,
        project_id=new_db_fake_build.project_id,
        build_request=build_request,
    )

    assert db_build == new_db_fake_build


def test_unique_build_not_found(db, new_db_fake_build):
    """
    GIVEN: A build in the database

    WHEN: Trying to get a build with a different configuration that does not exist

    THEN: None should be returned
    """
    build_request = StartBuildRequest(
        scheme="Release",
        test_plan="RP Swift",
        device_id=new_db_fake_build.device_id,
        configuration="Different Configuration",
    )

    db_build = get_unique_build(
        session=db,
        project_id=new_db_fake_build.project_id,
        build_request=build_request,
    )

    assert db_build is None


def test_create_build(db, new_db_project, new_db_fake_device):
    """
    GIVEN: A project in the database

    WHEN: Creating a new build

    THEN: The build should be created in the database and match the values passed and return value
    """
    build_request = StartBuildRequest(
        scheme="Release",
        test_plan="RP Swift",
        device_id=new_db_fake_device.id,
        configuration="Release",
    )

    db_build = create_build(
        session=db,
        project_id=new_db_project.id,
        build_request=build_request,
    )

    assert db_build.scheme == build_request.scheme
    assert db_build.configuration == build_request.configuration
    assert db_build.test_plan == build_request.test_plan
    assert db_build.project_id == new_db_project.id
    assert db_build.device_id == new_db_fake_device.id

    assert db_build == db.exec(select(Build).filter(Build.id == db_build.id)).one()


@pytest.mark.parametrize(
    "xcodebuild_fails",
    [
        (True,),
        (False,),
    ],
)
def test_start_build(
    db,
    xcodebuild_fails,
    new_db_project,
    random_device_id,
    new_db_fake_build,
    new_db_fake_xctestrun,
):
    """
    GIVEN: a build in the database
    AND: A job runner
    AND: A core AppBuilder
    AND: A job ID

    WHEN: Starting a build

    THEN: The build should be started
    AND: The job should be added to the job runner
    AND: The core AppBuilder should be called with the correct arguments
    """
    # fake build values in order to see if tested function changes them
    new_db_fake_build.status = "failed"
    new_db_fake_build.xctestrun = new_db_fake_xctestrun
    new_db_fake_build.xc_test_cases = ["Some/Test/case"]
    db.add(new_db_fake_build)
    db.commit()

    job_runner = AsyncJobRunner()
    app_builder = MagicMock(spec=AppBuilder)
    job_id = "job_id"

    with patch.object(job_runner, "add_job") as mock_add_job, patch(
        "api.services.project_service.build_output_dir"
    ) as mock_build_output_dir:
        mock_build_output_dir.return_value = pathlib.Path("/output_dir")

        start_build(
            session=db,
            job_runner=job_runner,
            db_build=new_db_fake_build,
            app_builder=app_builder,
            job_id=job_id,
        )

        mock_add_job.assert_called_once_with(
            _build_project_job,
            kwargs={
                "build_id": new_db_fake_build.id,
                "app_builder": app_builder,
                "output_dir": "/output_dir",
            },
            job_id=job_id,
        )

        db.refresh(new_db_fake_build)

        assert new_db_fake_build.status == "pending"
        assert new_db_fake_build.xctestrun is None
        assert new_db_fake_build.xc_test_cases is None


@pytest.mark.parametrize(
    "build_status_last_update",
    [
        "success",
        "failure",
    ],
)
@pytest.mark.asyncio
async def test_listen_to_build_updates(db, new_db_fake_build, build_status_last_update):
    """
    GIVEN: A build in the database
    AND: A method that creates a new build, updates it, updates the build that is being listened to a status that ends
    the listener

    WHEN: Listening to build updates

    THEN: Only the updates of the build should be listened to
    AND: The listener should stop
    """
    request_mock = AsyncMock(spec=Request)
    request_mock.is_disconnected.return_value = False

    async def simulate_updates():
        another_build = Build(
            project_id=new_db_fake_build.project_id,
            device_id=new_db_fake_build.device_id,
            scheme="Another Scheme",
            configuration="Another Configuration",
            test_plan="Another Test Plan",
            xctestrun=None,
        )
        db.add(another_build)
        db.commit()

        await asyncio.sleep(0.1)

        another_build.status = "running"
        db.add(another_build)
        db.commit()

        await asyncio.sleep(0.1)

        new_db_fake_build.status = build_status_last_update
        db.add(new_db_fake_build)
        db.commit()

    task = asyncio.create_task(simulate_updates())

    update_count = 0

    async for event in listen_to_build_updates(
        db_build=new_db_fake_build, request=request_mock
    ):
        update_count += 1

        # event is a json string and ends with two newlines and starts with "data: "
        assert event.endswith("\n\n")
        assert event.startswith("data: ")
        json_string = event[:-2].split("data: ")[1]
        assert BuildPublic.model_validate_json(json_string).id == new_db_fake_build.id

    await task

    assert update_count == 2
    request_mock.is_disconnected.assert_called()


@pytest.mark.asyncio
async def test_listen_to_build_updates_disconnect(db, new_db_fake_build):
    """
    GIVEN: A build in the database

    WHEN: Listening to build updates

    THEN: The listener should stop when the request is disconnected
    """
    request_mock = AsyncMock(spec=Request)
    request_mock.is_disconnected.side_effect = AsyncMock(return_value=True)

    async for event in listen_to_build_updates(
        db_build=new_db_fake_build, request=request_mock
    ):
        continue

    request_mock.is_disconnected.assert_called()

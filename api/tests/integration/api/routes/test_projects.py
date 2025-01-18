import asyncio
import pathlib
import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from api.models import (
    XcProject,
    XcProjectPublic,
    Build,
    BuildPublic,
)


def check_lists_equal(list_1: list, list_2: list) -> bool:
    """
    Check if two lists are equal.

    Copied from: https://safjan.com/pytest-check-lists-equal/
    """
    return len(list_1) == len(list_2) and sorted(list_1) == sorted(list_2)


def assert_real_project_values(
    project: XcProjectPublic, path_to_example_project: pathlib.Path
):
    """
    Assert the values of a public project object are correct and align with the example project in the roots misc
    folder.

    If the example project changes, the values in this function should be updated.
    """
    assert project.name == "RP Swift"
    assert project.path == path_to_example_project
    scheme_names = [scheme.name for scheme in project.schemes]
    assert check_lists_equal(scheme_names, ["Release", "RP Swift"])
    target_names = [target.name for target in project.targets]
    assert check_lists_equal(target_names, ["RP Swift", "RP SwiftUITests"])
    configuration_names = [
        configuration.name for configuration in project.configurations
    ]
    assert check_lists_equal(configuration_names, ["Debug", "Release"])
    for scheme in project.schemes:
        xc_test_plan_names = [
            xc_test_plan.name for xc_test_plan in scheme.xc_test_plans
        ]
        assert check_lists_equal(xc_test_plan_names, ["RP Swift"])


def test_list_projects(path_to_example_project, new_db_project, client):
    """
    GIVEN: A project in the database

    WHEN: GETing the `/projects` endpoint

    THEN: The response should contain a list of projects with the project inside
    AND: The project should have the correct values
    """
    r = client.get("/projects")

    assert r.status_code == 200

    projects = r.json()

    assert len(projects) >= 1

    found = False
    for project in projects:
        public_project = XcProjectPublic.model_validate(project)

        if public_project.path == path_to_example_project:
            found = True
            assert public_project == XcProjectPublic.model_validate(new_db_project)

    assert found


def test_read_project(path_to_example_project, new_db_project, client):
    """
    GIVEN: A project in the database

    WHEN: GETing the `/projects/{project_id}` endpoint

    THEN: It should return the requested project
    AND: The project should have the correct values
    """
    r = client.get(f"/projects/{new_db_project.id}")

    assert r.status_code == 200

    project = XcProjectPublic.model_validate(r.json())

    assert project == XcProjectPublic.model_validate(new_db_project)


def test_read_project_not_found(client):
    """
    GIVEN: No projects in the database

    WHEN: GETing the `/projects/{project_id}` endpoint with a non-existing project id

    THEN: The response should be a 404
    """
    r = client.get(f"/projects/{uuid.uuid4()}")

    assert r.status_code == 404


@pytest.mark.asyncio
async def test_add_project(db, path_to_example_project, client):
    """
    GIVEN: A project path

    WHEN: POSTing to the `/projects` endpoint with the project path

    THEN: It should add the project to the database
    AND: Return the project with the correct values
    """
    r = client.post(
        "/projects/",
        json={"path": str(path_to_example_project)},
    )

    assert r.status_code == 200

    public_project = XcProjectPublic.model_validate(r.json())

    db_project = db.get(XcProject, public_project.id)
    assert db_project is not None

    assert_real_project_values(public_project, path_to_example_project)


@pytest.mark.asyncio
async def test_add_project_invalid_path(client):
    """
    GIVEN: An invalid project path

    WHEN: POSTing to the `/projects` endpoint with the project path

    THEN: The response should be a 400
    """
    r = client.post(
        "/projects/",
        json={"path": str(pathlib.Path(__file__))},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_refresh_project(db, new_db_project, path_to_example_project, client):
    """
    GIVEN: A project in the database

    WHEN: POSTing to the `/projects/{project_id}/refresh` endpoint

    THEN: It should return the project with the correct values
    AND: It should update the project in the database and its related entities
    """
    old_project = XcProjectPublic.model_validate(new_db_project)

    r = client.post(f"/projects/{new_db_project.id}/refresh")

    assert r.status_code == 200

    refreshed_project = XcProjectPublic.model_validate(r.json())

    assert refreshed_project != old_project
    assert_real_project_values(refreshed_project, path_to_example_project)

    db.refresh(new_db_project)  # We need to refresh in order to get the latest db entry

    assert (
        XcProjectPublic.model_validate(db.get(XcProject, new_db_project.id))
        == refreshed_project
    )


@pytest.mark.asyncio
async def test_refresh_project_not_found(client):
    """
    GIVEN: No projects in the database

    WHEN: POSTing to the `/projects/{project_id}/refresh` endpoint with a non-existing project id

    THEN: The response should be a 404
    """
    r = client.post(f"/projects/{uuid.uuid4()}/refresh")

    assert r.status_code == 404


@pytest.mark.asyncio
async def test_refresh_project_invalid_path(db, new_db_project, client):
    """
    GIVEN: A project in the database with a non-existing path

    WHEN: POSTing to the `/projects/{project_id}/refresh` endpoint

    THEN: It should return the project as is
    """
    new_db_project.path = pathlib.Path(__file__)
    db.commit()

    r = client.post(f"/projects/{new_db_project.id}/refresh")

    assert r.status_code == 200

    refreshed_project = XcProjectPublic.model_validate(r.json())

    assert refreshed_project == XcProjectPublic.model_validate(new_db_project)


def test_list_builds(db, new_db_project, client, new_db_fake_device):
    """
    GIVEN: A project and a build in the database

    WHEN: GETing the `/projects/{project_id}/builds` endpoint

    THEN: The response should contain a list of at least one build
    AND: Contain the build that this test created
    AND: The build should have the correct values
    """
    db_build = Build(
        scheme="Release",
        configuration="Release",
        test_plan="RP Swift",
        project_id=new_db_project.id,
        device_id=new_db_fake_device.id,
    )
    db.add(db_build)
    db.commit()

    r = client.get(f"/projects/{new_db_project.id}/builds")

    assert r.status_code == 200

    builds = r.json()

    assert len(builds) >= 1

    found = False
    for build in builds:
        if build["id"] == str(db_build.id):
            found = True
            public_build = BuildPublic.model_validate(build)
            assert public_build == BuildPublic.model_validate(db_build)

    assert found


def test_read_build(db, new_db_project, client, new_db_fake_device):
    """
    GIVEN: A project and a build in the database

    WHEN: GETing the `/projects/{project_id}/builds/{build_id}` endpoint

    THEN: The response should contain the build
    AND: The build should have the correct values
    """
    db_build = Build(
        scheme="Release",
        configuration="Release",
        test_plan="RP Swift",
        project_id=new_db_project.id,
        device_id=new_db_fake_device.id,
    )
    db.add(db_build)
    db.commit()

    r = client.get(f"/projects/{new_db_project.id}/builds/{db_build.id}")

    assert r.status_code == 200

    public_build = BuildPublic.model_validate(r.json())

    assert public_build == BuildPublic.model_validate(db_build)


def test_read_build_not_found(client, new_db_project):
    """
    GIVEN: No matching builds in the database

    WHEN: GETing the `/projects/{project_id}/builds/{build_id}` endpoint with a non-existing build id

    THEN: The response should be a 404
    """
    r = client.get(f"/projects/{new_db_project.id}/builds/{uuid.uuid4()}")

    assert r.status_code == 404


def test_start_build(client, new_db_project, real_device):
    """
    GIVEN: A project in the database

    WHEN: POSTing to the `/projects/{project_id}/builds` endpoint

    THEN: The response should contain the build
    """
    if real_device is None:
        pytest.skip("No real device connected")

    with patch("api.routes.projects.project_service.start_build") as start_build_mock:
        # Mocking start build as we only want to test if the endpoint works up until this point
        r = client.post(
            f"/projects/{new_db_project.id}/builds",
            json={
                "scheme": new_db_project.schemes[0].name,
                "configuration": new_db_project.configurations[0].name,
                "test_plan": new_db_project.schemes[0].xc_test_plans[0].name,
                "device_id": real_device.udid,
            },
        )

        assert r.status_code == 200

        start_build_mock.assert_called_once()
        assert BuildPublic.model_validate(r.json())


def test_start_build_no_project(client, new_db_project, random_device_id):
    """
    GIVEN: No matching project in the database

    WHEN: POSTing to the `/projects/{project_id}/builds` endpoint

    THEN: The response should be a 404
    """
    r = client.post(
        f"/projects/{uuid.uuid4()}/builds",
        json={
            "scheme": new_db_project.schemes[0].name,
            "configuration": new_db_project.configurations[0].name,
            "test_plan": new_db_project.schemes[0].xc_test_plans[0].name,
            "device_id": random_device_id,
        },
    )

    assert r.status_code == 404


def test_start_build_invalid_request_data(client, new_db_project, random_device_id):
    """
    GIVEN: A project in the database

    WHEN: POSTing to the `/projects/{project_id}/builds` endpoint with invalid request data

    THEN: The response should be a 422
    """
    r = client.post(
        f"/projects/{new_db_project.id}/builds",
        json={
            "scheme": new_db_project.schemes[0].name,
            "configuration": "Invalid Configuration",
            "test_plan": new_db_project.schemes[0].xc_test_plans[0].name,
            "device_id": random_device_id,
        },
    )

    assert r.status_code == 422
    assert r.json() == {
        "detail": [
            {
                "loc": ["configuration"],
                "msg": "Invalid configuration",
            }
        ]
    }


def test_start_build_project_path_invalid(db, client, new_db_project):
    """
    GIVEN: A project in the database
    AND: The projects path is now invalid (e.g. was deleted)

    WHEN: POSTing to the `/projects/{project_id}/builds` endpoint

    THEN: The response should be a 400
    """
    new_db_project.path = pathlib.Path(__file__)
    db.add(new_db_project)
    db.commit()

    r = client.post(
        f"/projects/{new_db_project.id}/builds",
        json={
            "scheme": new_db_project.schemes[0].name,
            "configuration": new_db_project.configurations[0].name,
            "test_plan": new_db_project.schemes[0].xc_test_plans[0].name,
            "device_id": "invalid_device_id",
        },
    )

    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid project path"}


def test_start_build_invalid_device(client, new_db_project):
    """
    GIVEN: A project in the database

    WHEN: POSTing to the `/projects/{project_id}/builds` endpoint with a device id that cannot be found

    THEN: The response should be a 404
    """
    r = client.post(
        f"/projects/{new_db_project.id}/builds",
        json={
            "scheme": new_db_project.schemes[0].name,
            "configuration": new_db_project.configurations[0].name,
            "test_plan": new_db_project.schemes[0].xc_test_plans[0].name,
            "device_id": "invalid_device_id",
        },
    )

    assert r.status_code == 404
    assert r.json() == {"detail": "Device not found"}


def test_start_build_existing_build(db, client, new_db_project, real_device):
    """
    GIVEN: A project in the database

    WHEN: POSTing to the `/projects/{project_id}/builds` endpoint TWICE with the same data

    THEN: There should be no error (We mock the start build as we only care about the behaviour of "rebuilding").
    """
    if real_device is None:
        pytest.skip("No real device connected")

    request_data = {
        "scheme": new_db_project.schemes[0].name,
        "configuration": new_db_project.configurations[0].name,
        "test_plan": new_db_project.schemes[0].xc_test_plans[0].name,
        "device_id": real_device.udid,
    }

    with patch("api.routes.projects.project_service.start_build") as start_build_mock:
        r = client.post(
            f"/projects/{new_db_project.id}/builds",
            json=request_data,
        )

        r_2 = client.post(
            f"/projects/{new_db_project.id}/builds",
            json=request_data,
        )

        assert r.status_code == 200
        assert r_2.status_code == 200

        assert r.json() == r_2.json()

        assert start_build_mock.call_count == 2


@pytest.mark.asyncio
async def test_stream_build_updates_not_found(async_client: AsyncClient):
    """
    GIVEN: No matching project or build in the database

    WHEN: GETing the `/projects/{project_id}/builds/{build_id}/update-stream` endpoint

    THEN: The response should be a 404
    """
    r = await async_client.get(
        f"/projects/{uuid.uuid4()}/builds/{uuid.uuid4()}/update-stream"
    )

    assert r.status_code == 404


@pytest.mark.asyncio
async def test_stream_build_updates(db, async_client: AsyncClient, new_db_fake_build):
    """
    GIVEN: A matching project and build in the database

    WHEN: GETing the `/projects/{project_id}/builds/{build_id}/update-stream` endpoint
    AND: The status is updated to "success"

    THEN: The response should be a 200
    AND: The response should contain two builds. One with status "pending" and one with status "success"
    """
    # TODO: It's not that easy to currently test SSE events (stream). In this test we're simply waiting for all data
    #  to have arrived. See issue: https://github.com/encode/httpx/issues/2186.

    async def simulate_update():
        await asyncio.sleep(0.1)
        new_db_fake_build.status = "success"
        db.add(new_db_fake_build)
        db.commit()

    task = asyncio.create_task(simulate_update())

    r = await async_client.get(
        f"/projects/{new_db_fake_build.project_id}/builds/{new_db_fake_build.id}/update-stream",
    )

    await task

    assert r.status_code == 200

    lines = r.text.split("\n\n")
    assert len(lines) == 3

    for index, line in enumerate(lines):
        if index == 0:
            assert BuildPublic.model_validate_json(line).status == "pending"
        elif index == 1:
            assert BuildPublic.model_validate_json(line).status == "success"
        else:
            assert line == ""

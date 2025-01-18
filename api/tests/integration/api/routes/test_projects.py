import pathlib
import uuid

import pytest

from api.models import (
    XcProject,
    XcProjectScheme,
    XcProjectTarget,
    XcProjectConfiguration,
    XcProjectTestPlan,
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


@pytest.fixture
def new_db_project(db, path_to_example_project):
    project = XcProject(name="project_1", path=path_to_example_project)
    db.add(project)
    db.commit()

    scheme = XcProjectScheme(name="scheme_1", project_id=project.id)
    target = XcProjectTarget(name="target_1", project_id=project.id)
    configuration = XcProjectConfiguration(
        name="configuration_1", project_id=project.id
    )
    db.add(scheme)
    db.add(target)
    db.add(configuration)
    db.commit()

    xc_test_plan = XcProjectTestPlan(
        name="xc_test_plan_1", scheme_id=scheme.id, project_id=project.id
    )
    db.add(xc_test_plan)
    db.commit()

    return project


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

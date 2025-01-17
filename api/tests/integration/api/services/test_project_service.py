import pathlib
import uuid

import pytest
from fastapi import HTTPException

from api.models import (
    XcProject,
    XcProjectScheme,
    XcProjectTarget,
    XcProjectConfiguration,
    XcProjectTestPlan,
    XcProjectPublic,
    XcProjectCreate,
)
from api.services.project_service import list_projects, read_project, add_project


def check_lists_equal(list_1: list, list_2: list) -> bool:
    """
    Check if two lists are equal.

    Copied from: https://safjan.com/pytest-check-lists-equal/
    """
    return len(list_1) == len(list_2) and sorted(list_1) == sorted(list_2)


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


def test_list_projects(db, path_to_example_project, new_db_project):
    """
    GIVEN: A database with a project

    WHEN: list_projects is called

    THEN: It should return a list of projects with the project inside
    AND: The project should have the correct values
    """
    projects = list_projects(session=db)

    assert len(projects) >= 1

    found = False
    for project in projects:
        if project.path == path_to_example_project:
            found = True
            assert project == XcProjectPublic.model_validate(new_db_project)

    assert found


def test_read_project(db, path_to_example_project, new_db_project):
    """
    GIVEN: A database with a project

    WHEN: read_project is called with the project id

    THEN: It should return the requested project
    AND: The project should have the correct values
    """
    project = read_project(session=db, project_id=new_db_project.id)

    assert project == XcProjectPublic.model_validate(new_db_project)


def test_read_project_not_found(db):
    """
    GIVEN: A database with no projects

    WHEN: read_project is called with a non-existing project id

    THEN: It should raise a 404 HTTPException
    """
    with pytest.raises(HTTPException) as e:
        read_project(session=db, project_id=uuid.uuid4())
    assert e.value.status_code == 404


@pytest.mark.asyncio
async def test_add_project(db, path_to_example_project):
    """
    GIVEN: A project path

    WHEN: add_project is called with the project path

    THEN: It should add the project to the database
    AND: Return the project with the correct values
    """
    public_project = await add_project(
        session=db, project=XcProjectCreate(path=path_to_example_project)
    )

    db_project = db.get(XcProject, public_project.id)
    assert db_project is not None

    assert public_project.name == "RP Swift"
    assert public_project.path == path_to_example_project
    scheme_names = [scheme.name for scheme in public_project.schemes]
    assert check_lists_equal(scheme_names, ["Release", "RP Swift"])
    target_names = [target.name for target in public_project.targets]
    assert check_lists_equal(target_names, ["RP Swift", "RP SwiftUITests"])
    configuration_names = [
        configuration.name for configuration in public_project.configurations
    ]
    assert check_lists_equal(configuration_names, ["Debug", "Release"])
    for scheme in public_project.schemes:
        xc_test_plan_names = [
            xc_test_plan.name for xc_test_plan in scheme.xc_test_plans
        ]
        assert check_lists_equal(xc_test_plan_names, ["RP Swift"])


@pytest.mark.asyncio
async def test_add_project_invalid_path(db):
    """
    GIVEN: An invalid project path

    WHEN: add_project is called with the project path

    THEN: It should raise a 404 HTTPException
    """
    with pytest.raises(HTTPException) as e:
        await add_project(
            session=db, project=XcProjectCreate(path=pathlib.Path(__file__))
        )
    assert e.value.status_code == 400

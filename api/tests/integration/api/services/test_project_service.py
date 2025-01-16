import uuid

import pytest
from fastapi import HTTPException

from api.models import (
    XcProject,
    XcProjectSchema,
    XcProjectTarget,
    XcProjectConfiguration,
    XcProjectTestPlan,
    XcProjectPublic,
)
from api.services.project_service import list_projects, read_project


@pytest.fixture
def new_db_project(db, path_to_example_project):
    project = XcProject(name="project_1", path=path_to_example_project)
    db.add(project)
    db.commit()

    schema = XcProjectSchema(name="schema_1", project_id=project.id)
    target = XcProjectTarget(name="target_1", project_id=project.id)
    configuration = XcProjectConfiguration(
        name="configuration_1", project_id=project.id
    )
    db.add(schema)
    db.add(target)
    db.add(configuration)
    db.commit()

    xc_test_plan = XcProjectTestPlan(
        name="xc_test_plan_1", schema_id=schema.id, project_id=project.id
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

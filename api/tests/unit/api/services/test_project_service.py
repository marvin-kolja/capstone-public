import random
import uuid
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from sqlmodel import Session

from api.models import (
    XcProjectResourceModel,
    XcProjectConfiguration,
    XcProjectTestPlan,
    XcProjectScheme,
    XcProjectTarget,
    XcProject,
)
from api.services.project_service import sync_project_resources, sync_db_project
from core.xc import xc_project as core_xc_project


def gen_random_list_of_integers(
    int_start: int = 1,
    int_end: int = 10,
    list_start: int = 1,
    list_end: int = 10,
) -> list[int]:
    """
    Generates a random list of integers between 1 and 10 with a random length between 1 and 10

    List does not contain duplicates
    """
    return list(
        set(
            random.choices(
                range(int_start, int_end), k=random.randint(list_start, list_end)
            )
        )
    )


@pytest.mark.parametrize(
    "model_class, additional_fields",
    [
        (XcProjectConfiguration, {}),
        (XcProjectTarget, {}),
        (XcProjectScheme, {}),
        (XcProjectTestPlan, {"scheme_id": uuid.uuid4()}),
    ],
)
@pytest.mark.parametrize(
    "resource_numbers, number_of_new_resources",
    [
        (
            gen_random_list_of_integers(list_start=5),
            gen_random_list_of_integers(int_start=5, int_end=15, list_start=5),
        )
        for _ in range(
            5
        )  # Generate n random test cases with random number of resources
    ],
)
def test_sync_resources(
    model_class, additional_fields, resource_numbers, number_of_new_resources
):
    """
    GIVEN: a mocked db session
    AND: and list of project resource models
    AND: a list of new project recourse names
    AND: a project id

    WHEN: sync_resources is called

    THEN: The correct amounts of resources are added and deleted from the database
    AND: The correct values are added to the database
    AND: The correct values are removed from the database
    """
    db_session_mock = MagicMock(spec=Session)
    project_id = uuid.uuid4()

    project_resources = [
        XcProjectResourceModel(name=f"resource{num}", project_id=project_id)
        for num in resource_numbers
    ]

    new_project_resources = [f"resource{num}" for num in number_of_new_resources]

    overlaps = set(new_project_resources).intersection(
        set([resource.name for resource in project_resources])
    )  # Calculate how many resources are already in the database
    count_of_deleted = len(project_resources) - len(
        overlaps
    )  # Calculate how many resources need to be deleted
    count_of_new = len(new_project_resources) - len(
        overlaps
    )  # Calculate how many resources need to be created

    sync_project_resources(
        session=db_session_mock,
        db_items=project_resources,
        new_item_names=new_project_resources,
        project_id=project_id,
        model_class=model_class,
        additional_fields=additional_fields,
    )

    assert db_session_mock.add.call_count == count_of_new
    assert db_session_mock.delete.call_count == count_of_deleted

    for _call in db_session_mock.add.call_args_list:
        db_model = _call.args[0]

        assert isinstance(db_model, model_class)
        assert db_model.name in new_project_resources
        assert db_model.name not in overlaps
        assert db_model.project_id == project_id
        if additional_fields:
            for key, value in additional_fields.items():
                assert getattr(db_model, key) == value

    for _call in db_session_mock.delete.call_args_list:
        db_model = _call.args[0]

        assert isinstance(db_model, XcProjectResourceModel)
        assert db_model.name not in new_project_resources
        assert db_model.name not in overlaps


@pytest.mark.asyncio
async def test_sync_db_project():
    """
    GIVEN: a mocked db session
    AND: a mocked XcProject from `core`

    WHEN: sync_db_project is called

    THEN: The sync_project_resources is called with the correct parameters for all data
    AND: The name of the project is updated
    """
    with patch(
        "api.services.project_service.sync_project_resources"
    ) as sync_project_resources_mock:

        db_session_mock = MagicMock(spec=Session)
        db_project_mock = MagicMock(spec=XcProject)
        db_project_mock.name = "Old Name"
        db_project_mock.schemes = [
            MagicMock(spec=XcProjectScheme),
            MagicMock(spec=XcProjectScheme),
        ]

        core_xc_project_mock = AsyncMock(spec=core_xc_project.XcProject)

        core_project_details_mock = MagicMock(spec=core_xc_project.ProjectDetails)
        core_project_details_mock.name = "Project Name"
        core_project_details_mock.configurations = MagicMock(spec=list)
        core_project_details_mock.targets = MagicMock(spec=list)
        core_project_details_mock.schemes = MagicMock(spec=list)

        core_xc_project_mock.list.return_value = core_project_details_mock
        core_xc_project_mock.xcode_test_plans.return_value = [
            MagicMock(spec=str),
            MagicMock(spec=str),
        ]

        await sync_db_project(
            session=db_session_mock,
            db_project=db_project_mock,
            xc_project=core_xc_project_mock,
        )

        assert (
            sync_project_resources_mock.call_count == 5
        )  # 3 resources + For each scheme to sync test plans (2 schemes)

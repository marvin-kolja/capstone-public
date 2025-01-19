import pathlib
import random
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock, call

import pytest
from core.xc.app_builder import AppBuilder
from core.xc.commands.xcodebuild_command import IOSDestination
from core.xc.xctestrun import Xctestrun, XcTestConfiguration, XcTestTarget
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session

from api.models import (
    XcProjectResourceModel,
    XcProjectConfiguration,
    XcProjectTestPlan,
    XcProjectScheme,
    XcProjectTarget,
    XcProject,
    StartBuildRequest,
    Build,
)
from api.services.project_service import (
    sync_project_resources,
    sync_db_project,
    validate_build_request,
    _build_project_job,
)
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

    return_value = sync_project_resources(
        session=db_session_mock,
        db_items=project_resources,
        new_item_names=new_project_resources,
        project_id=project_id,
        model_class=model_class,
        additional_fields=additional_fields,
    )

    assert db_session_mock.add.call_count == count_of_new
    assert db_session_mock.delete.call_count == count_of_deleted

    assert len(return_value) == len(new_project_resources)

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

        sync_project_resources_mock.side_effect = [
            [MagicMock(spec=XcProjectConfiguration)],  # First call
            [MagicMock(spec=XcProjectTarget)],  # Second call
            [
                MagicMock(spec=XcProjectScheme),
                MagicMock(spec=XcProjectScheme),
            ],  # Third call
            [
                MagicMock(spec=XcProjectTestPlan),
                MagicMock(spec=XcProjectTestPlan),
            ],  # Fourth call
            [
                MagicMock(spec=XcProjectTestPlan),
                MagicMock(spec=XcProjectTestPlan),
            ],  # Fifth call
        ]

        await sync_db_project(
            session=db_session_mock,
            db_project=db_project_mock,
            xc_project=core_xc_project_mock,
        )

        assert (
            sync_project_resources_mock.call_count == 5
        )  # 3 resources + For each scheme to sync test plans (2 schemes)


@pytest.mark.parametrize(
    "scheme_name, test_plan_name, configuration, expected_error",
    [
        ("scheme", "test_plan", "configuration", None),
        (
            "scheme",
            "test_plan",
            "invalid_configuration",
            {"loc": ["configuration"], "msg": "Invalid configuration"},
        ),
        (
            "scheme",
            "invalid_test_plan",
            "configuration",
            {"loc": ["test_plan"], "msg": "Invalid test plan"},
        ),
        (
            "invalid_scheme",
            "test_plan",
            "configuration",
            {"loc": ["scheme"], "msg": "Invalid scheme"},
        ),
    ],
)
def test_validate_build_request(
    scheme_name, test_plan_name, configuration, expected_error, random_device_id
):
    """
    GIVEN: A valid or invalid build request

    WHEN: validate_build_request is called

    THEN: A RequestValidationError is raised if the build request is invalid
    AND: No exception is raised if the build request is valid
    """
    xc_test_plan = MagicMock(spec=XcProjectTestPlan)
    xc_test_plan.name = "test_plan"

    xc_scheme = MagicMock(spec=XcProjectScheme)
    xc_scheme.name = "scheme"
    xc_scheme.xc_test_plans = [xc_test_plan]

    xc_configuration = MagicMock(spec=XcProjectConfiguration)
    xc_configuration.name = "configuration"

    build = MagicMock(spec=XcProject)
    build.schemes = [xc_scheme]
    build.configurations = [xc_configuration]

    build_request = StartBuildRequest(
        scheme=scheme_name,
        test_plan=test_plan_name,
        device_id=random_device_id,
        configuration=configuration,
    )

    if expected_error is not None:
        with pytest.raises(RequestValidationError) as e:
            validate_build_request(db_project=build, build_request=build_request)
        assert e.value.errors() == [expected_error]
    else:
        validate_build_request(db_project=build, build_request=build_request)


@pytest.mark.parametrize(
    "app_path_exists_after_first_build",
    [
        True,
        False,
    ],
)
@pytest.mark.asyncio
async def test_build_project_job(random_device_id, app_path_exists_after_first_build):
    """
    GIVEN: A mocked db session
    AND: A mocked AppBuilder from `core`
    AND: A mocked Build model instance
    AND: A mocked `Xctest.parse_xctestrun` method

    WHEN: _build_project_job is called

    THEN: The app_builder.build_for_testing is called with the correct parameters
    AND: The app_builder.build is called with the correct parameters if required
    """
    db_session_mock = MagicMock(spec=Session)
    app_builder_mock = MagicMock(spec=AppBuilder)

    build_mock = MagicMock(spec=Build)
    status_value_mock = PropertyMock()
    type(build_mock).status = status_value_mock
    build_mock.test_plan = "test_plan"
    build_mock.device_id = random_device_id
    build_mock.configuration = "configuration"
    build_mock.scheme = "scheme"

    xctestrun_mock = MagicMock(spec=Xctestrun)
    test_target_mock = MagicMock(spec=XcTestTarget)
    test_target_mock.app_path = "/app_path"
    test_configuration_mock = MagicMock(spec=XcTestConfiguration)
    test_configuration_mock.Name = "Some Test Configuration"
    test_configuration_mock.TestTargets = [test_target_mock]
    xctestrun_mock.TestConfigurations = [test_configuration_mock]

    with patch("api.services.project_service.Xctest") as xctest_mock, patch.object(
        Path, "exists"
    ) as path_exists_mock, patch(
        "api.services.project_service.Xctestrun"
    ) as xctestrun_model_mock:
        xctest_mock.parse_xctestrun.return_value = xctestrun_mock
        path_exists_mock.return_value = app_path_exists_after_first_build

        await _build_project_job(
            session=db_session_mock,
            app_builder=app_builder_mock,
            db_build=build_mock,
            output_dir="output_dir",
        )

        app_builder_mock.build_for_testing.assert_awaited_once_with(
            configuration=build_mock.configuration,
            scheme=build_mock.scheme,
            destination=IOSDestination(id=build_mock.device_id),
            test_plan=build_mock.test_plan,
            output_dir="output_dir",
            clean=True,
        )

        if not app_path_exists_after_first_build:
            app_builder_mock.build.assert_awaited_once_with(
                configuration=build_mock.configuration,
                scheme=build_mock.scheme,
                destination=IOSDestination(id=build_mock.device_id),
                output_dir="output_dir",
                clean=False,
            )

        status_value_mock.assert_has_calls(
            [
                call("running"),
                call("success"),
            ]
        )

        xctestrun_model_mock.assert_called_once_with(
            path=pathlib.Path(
                app_builder_mock.build_for_testing.return_value.xctestrun_path
            ),
            test_configurations=[xctestrun_mock.TestConfigurations[0].Name],
            build_id=build_mock.id,
        )

        # 1 for start, 1 for adding xctestrun, 1 for adding build
        assert db_session_mock.add.call_count == 3
        assert db_session_mock.commit.call_count == 3


@pytest.mark.asyncio
async def test_build_project_job_failure(random_device_id):
    """
    GIVEN: A mocked db session
    AND: A mocked AppBuilder from `core`
    AND: A mocked Build model instance

    WHEN: _build_project_job is called and the build_for_testing fails

    THEN: The db build entry should have a failed status
    """
    db_session_mock = MagicMock(spec=Session)
    app_builder_mock = MagicMock(spec=AppBuilder)

    build_mock = MagicMock(spec=Build)
    status_mock = PropertyMock()
    type(build_mock).status = status_mock
    build_mock.device_id = random_device_id

    app_builder_mock.build_for_testing.side_effect = Exception("Failed to build")

    await _build_project_job(
        session=db_session_mock,
        app_builder=app_builder_mock,
        db_build=build_mock,
        output_dir="output_dir",
    )

    status_mock.assert_has_calls(
        [
            call("running"),
            call("failure"),
        ]
    )

    # 1 for start, 1 for failure
    assert db_session_mock.add.call_count == 2
    assert db_session_mock.commit.call_count == 2

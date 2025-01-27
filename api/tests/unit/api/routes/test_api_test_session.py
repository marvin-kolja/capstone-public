import uuid
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from core.device.i_device import IDeviceStatus
from core.device.i_device_manager import IDeviceManager
from fastapi import HTTPException
from sqlmodel import Session

from api.async_jobs import AsyncJobRunner
from api.depends import get_job_runner
from api.main import app
from api.models import (
    Build,
    SessionTestPlan,
    TestSessionCreate,
    DeviceWithStatus,
    BuildPublic,
    SessionTestPlanPublic,
)

# noinspection PyProtectedMember
from api.routes.api_test_session import _validate_test_session_input, start_test_session
from api.services import api_test_session_service


@pytest.mark.asyncio
async def test_start_test_session():
    """
    GIVEN: The start test session endpoint method

    WHEN: The method is called with mocked dependencies

    THEN: The method should return the created test session
    AND: The method should call all the necessary methods with the correct arguments
    """

    # NOTE: This is a very complex test case. It simply makes sure that the method calls all the necessary methods with
    #  the correct arguments. Each of the called methods are tested separately in their own test cases.

    session = MagicMock()
    job_runner = AsyncMock()
    device_manager = MagicMock()
    session_create = TestSessionCreate(
        build_id=uuid.uuid4(),
        plan_id=uuid.uuid4(),
        xc_test_configuration_name="TestConfig",
    )

    mock_public_build = MagicMock()
    mock_public_plan = MagicMock()
    mock_public_device = MagicMock()

    mock_execution_plan = MagicMock()
    mock_execution_steps = MagicMock()
    mock_db_test_session = MagicMock()

    with (
        patch(
            "api.routes.api_test_session._validate_test_session_input",
            return_value=(mock_public_build, mock_public_plan, mock_public_device),
        ) as mock_validate,
        patch.object(
            api_test_session_service, "plan_execution", return_value=mock_execution_plan
        ) as mock_plan_execution,
        patch.object(
            api_test_session_service, "generate_session_id", return_value=uuid.uuid4()
        ) as mock_generate_id,
        patch.object(
            api_test_session_service,
            "construct_db_execution_step_models",
            return_value=mock_execution_steps,
        ) as mock_construct_steps,
        patch.object(
            api_test_session_service,
            "create_test_session",
            return_value=mock_db_test_session,
        ) as mock_create_test_session,
        patch.object(
            api_test_session_service, "start_test_session", return_value=None
        ) as mock_start_session,
        patch.object(
            device_manager, "get_device", return_value=MagicMock()
        ) as mock_get_device,
    ):

        result = await start_test_session(
            session=session,
            job_runner=job_runner,
            device_manager=device_manager,
            session_create=session_create,
        )

        assert result == mock_db_test_session

        # Ensure all mocked methods were called
        mock_validate.assert_called_once_with(
            session=session,
            device_manager=device_manager,
            session_create=session_create,
        )
        mock_plan_execution.assert_called_once_with(
            public_plan=mock_public_plan,
            xctestrun_path=mock_public_build.xctestrun.path,
            xc_test_configuration_name=session_create.xc_test_configuration_name,
        )
        mock_construct_steps.assert_called_once_with(
            test_session_id=mock_generate_id.return_value,
            core_execution_plan=mock_execution_plan,
        )
        mock_create_test_session.assert_called_once_with(
            session=session,
            public_plan=mock_public_plan,
            public_build=mock_public_build,
            public_device=mock_public_device,
            execution_steps=mock_execution_steps,
            session_id=mock_generate_id.return_value,
            xc_test_configuration_name=session_create.xc_test_configuration_name,
        )
        mock_start_session.assert_called_once_with(
            job_runner=job_runner,
            test_session_id=mock_generate_id.return_value,
            core_execution_plan=mock_execution_plan,
            i_device=mock_get_device.return_value,
        )

        mock_get_device.assert_called_once_with(mock_public_device.id)


@pytest.fixture
def mock_async_job_runner_dependency():
    mock_job_runner = MagicMock(spec=AsyncJobRunner)

    async def override_job_runner():
        return mock_job_runner

    app.dependency_overrides[get_job_runner] = override_job_runner

    yield mock_job_runner

    app.dependency_overrides = {}


def test_cancel_test_session(client, mock_async_job_runner_dependency):
    """
    GIVEN: a running test session

    WHEN: the test session is cancelled

    THEN: the test session should be cancelled
    """
    fake_test_session_id = uuid.uuid4()

    mock_db_test_session = MagicMock()
    mock_db_test_session.id = fake_test_session_id

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=mock_db_test_session,
    ) as mock_read_test_session:

        r = client.post(
            f"/test-sessions/{fake_test_session_id}/cancel",
        )

        assert r.status_code == 200, r.text

        mock_read_test_session.assert_called_once()

        mock_async_job_runner_dependency.job_exists.assert_called_once_with(
            job_id=fake_test_session_id.hex
        )
        mock_async_job_runner_dependency.cancel_job.assert_called_once_with(
            job_id=fake_test_session_id.hex
        )


def test_cancel_test_session_test_session_not_found(client):
    """
    GIVEN: a test session that does not exist

    WHEN: the test session is cancelled

    THEN: a 404 error should be returned
    """
    fake_test_session_id = uuid.uuid4()

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=None,
    ) as mock_read_test_session:

        r = client.post(
            f"/test-sessions/{fake_test_session_id}/cancel",
        )

        assert r.status_code == 404, r.text

        mock_read_test_session.assert_called_once()


def test_cancel_test_session_test_session_not_running(
    client, mock_async_job_runner_dependency
):
    """
    GIVEN: a test session that is not running

    WHEN: the test session is cancelled

    THEN: a 400 error should be returned
    """
    fake_test_session_id = uuid.uuid4()

    mock_db_test_session = MagicMock()
    mock_db_test_session.id = fake_test_session_id

    mock_async_job_runner_dependency.job_exists.return_value = False

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=mock_db_test_session,
    ):

        r = client.post(
            f"/test-sessions/{fake_test_session_id}/cancel",
        )

        assert r.status_code == 400, r.text

        mock_async_job_runner_dependency.job_exists.assert_called_once_with(
            job_id=fake_test_session_id.hex
        )


def test_stream_execution_step_updates_test_session_not_found(client):
    """
    GIVEN: a test session that does not exist

    WHEN: the execution step updates are streamed

    THEN: a 404 error should be returned
    """
    fake_test_session_id = uuid.uuid4()

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=None,
    ) as mock_read_test_session:

        r = client.get(
            f"/test-sessions/{fake_test_session_id}/execution-step-stream",
        )

        assert r.status_code == 404, r.text

        mock_read_test_session.assert_called_once()


@pytest.mark.parametrize(
    "status",
    [
        "completed",
        "failed",
        "cancelled",
    ],
)
def test_stream_execution_step_updates_test_session_not_running(client, status):
    """
    GIVEN: a test session that is completed

    WHEN: the execution step updates are streamed

    THEN: a 400 error should be returned
    """
    fake_test_session_id = uuid.uuid4()

    mock_db_test_session = MagicMock()
    mock_db_test_session.id = fake_test_session_id
    mock_db_test_session.status = "completed"

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=mock_db_test_session,
    ) as mock_read_test_session:

        r = client.get(
            f"/test-sessions/{fake_test_session_id}/execution-step-stream",
        )

        assert r.status_code == 400, r.text

        mock_read_test_session.assert_called_once()


def test_export_test_session_results_not_found(client):
    """
    GIVEN: a test session that does not exist

    WHEN: POSTing to `/test-sessions/{test_session_id}/export-results`

    THEN: a 404 error should be returned
    """
    fake_test_session_id = uuid.uuid4()

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=None,
    ) as mock_read_test_session:

        r = client.post(
            f"/test-sessions/{fake_test_session_id}/process-trace-results",
        )

        assert r.status_code == 404, r.text

        mock_read_test_session.assert_called_once()


def test_export_test_session_results_not_completed(client):
    """
    GIVEN: a test session that is not completed

    WHEN: POSTing to `/test-sessions/{test_session_id}/process-trace-results`

    THEN: a 400 error should be returned
    """
    fake_test_session_id = uuid.uuid4()

    mock_db_test_session = MagicMock()
    mock_db_test_session.id = fake_test_session_id
    mock_db_test_session.status = "in_progress"

    with patch(
        "api.routes.api_test_session.api_test_session_service.read_test_session",
        return_value=mock_db_test_session,
    ) as mock_read_test_session:
        r = client.post(
            f"/test-sessions/{fake_test_session_id}/process-trace-results",
        )

        assert r.status_code == 400, r.text

        mock_read_test_session.assert_called_once()


def test_export_test_session_results_200(client, mock_async_job_runner_dependency):
    """
    GIVEN: a test session that is completed

    WHEN: POSTing to `/test-sessions/{test_session_id}/process-trace-results`

    THEN: a 200 response should be returned
    """
    fake_test_session_id = uuid.uuid4()

    mock_db_test_session = MagicMock()
    mock_db_test_session.id = fake_test_session_id
    mock_db_test_session.status = "completed"

    with (
        patch(
            "api.routes.api_test_session.api_test_session_service.read_test_session",
            return_value=mock_db_test_session,
        ) as mock_read_test_session,
        patch(
            "api.routes.api_test_session.api_test_session_service.process_trace_results",
        ) as mock_process_results,
    ):

        r = client.post(
            f"/test-sessions/{fake_test_session_id}/process-trace-results",
        )

        assert r.status_code == 200, r.text

        mock_read_test_session.assert_called_once()
        mock_process_results.assert_called_once_with(
            test_session_id=fake_test_session_id,
            job_runner=mock_async_job_runner_dependency,
        )


@pytest.fixture
def fake_project_id():
    return uuid.uuid4()


@pytest.fixture
def fake_device_with_status(random_device_id):
    db_device_mock = MagicMock(spec=DeviceWithStatus)
    db_device_mock.id = random_device_id
    db_device_mock.name = "fake_device_name"
    db_device_mock.connected = True

    status_mock = MagicMock(spec=IDeviceStatus)
    status_mock.tunnel_connected = True
    db_device_mock.status = status_mock

    return db_device_mock


@pytest.fixture
def fake_db_build(fake_project_id):
    db_build_mock = MagicMock(spec=Build)
    db_build_mock.id = uuid.uuid4()
    db_build_mock.project_id = fake_project_id
    db_build_mock.test_plan = "fake_plan_name"
    db_build_mock.status = "success"
    db_build_mock.xctestrun.test_configurations = ["fake_test_config"]
    return db_build_mock


@pytest.fixture
def fake_db_plan(fake_project_id):
    db_plan_mock = MagicMock(spec=SessionTestPlan)
    db_plan_mock.id = uuid.uuid4()
    db_plan_mock.project_id = fake_project_id
    db_plan_mock.xc_test_plan_name = "fake_plan_name"
    return db_plan_mock


@pytest.fixture
def mock_get_device_by_id(fake_device_with_status):
    with patch("api.routes.api_test_session.device_service.get_device_by_id") as mock:
        mock.return_value = fake_device_with_status
        yield mock


@pytest.fixture
def mock_read_build(fake_db_build):
    with patch("api.routes.api_test_session.project_service.read_build") as mock:
        mock.return_value = fake_db_build
        yield mock


@pytest.fixture
def mock_read_test_plan(fake_db_plan):
    with patch(
        "api.routes.api_test_session.api_test_plan_service.read_test_plan"
    ) as mock:
        mock.return_value = fake_db_plan
        yield mock


@pytest.fixture
def test_session_create(fake_db_plan):
    return TestSessionCreate(
        plan_id=fake_db_plan.id,
        xc_test_configuration_name="fake_test_config",
    )


def test_validate_test_session_input_db_build_not_found(
    mock_read_build, test_session_create
):
    mock_read_build.return_value = None

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 500


def test_validate_test_session_input_db_plan_not_found(
    mock_read_test_plan, test_session_create
):
    mock_read_test_plan.return_value = None

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Invalid plan id"


def test_validate_test_session_input_build_and_plan_not_same_project(
    test_session_create, mock_read_build, mock_read_test_plan, fake_db_plan
):
    fake_db_plan.project_id = uuid.uuid4()

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Plan and build must belong to the same project"


def test_validate_test_session_input_build_is_part_of_project(
    test_session_create, mock_read_build, mock_read_test_plan, fake_db_plan
):
    mock_read_build.return_value.project_id = uuid.uuid4()

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Plan and build must belong to the same project"


def test_validate_test_session_input_build_not_completed(
    test_session_create, mock_read_build, mock_read_test_plan, fake_db_build
):
    fake_db_build.status = "in_progress"

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Build must be completed"


def test_validate_test_session_input_xc_test_configuration_not_in_build(
    test_session_create, mock_read_build, mock_read_test_plan, fake_db_build
):
    test_session_create.xc_test_configuration_name = "different_test_config"

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Invalid test configuration name"


def test_validate_test_session_input_xctestrun_path_not_exists(
    test_session_create, mock_read_build, mock_read_test_plan, fake_db_build
):
    fake_db_build.xctestrun.path.exists.return_value = False

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Xctestrun file not found. Try rebuilding the project"


def test_validate_test_session_input_device_not_found(
    test_session_create, mock_read_build, mock_read_test_plan, mock_get_device_by_id
):
    mock_get_device_by_id.return_value = None

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Device not connected"


def test_validate_test_session_input_device_not_connected(
    test_session_create, mock_read_build, mock_read_test_plan, mock_get_device_by_id
):
    mock_get_device_by_id.return_value.connected = False

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "Device not connected"


def test_validate_test_session_input_device_tunnel_not_connected(
    test_session_create, mock_read_build, mock_read_test_plan, mock_get_device_by_id
):
    mock_get_device_by_id.return_value.status.tunnel_connected = False

    with pytest.raises(HTTPException) as e:
        _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

    assert e.value.status_code == 400
    assert e.value.detail == "No tunnel connection to the device"


def test_validate_test_session_input_valid(
    test_session_create, mock_read_build, mock_read_test_plan, mock_get_device_by_id
):
    with (
        patch.object(BuildPublic, "model_validate") as mock_build_public_validate,
        patch.object(
            SessionTestPlanPublic, "model_validate"
        ) as mock_plan_public_validate,
    ):
        mock_build_public_validate.return_value = MagicMock(spec=BuildPublic)
        mock_plan_public_validate.return_value = MagicMock(spec=SessionTestPlanPublic)

        result = _validate_test_session_input(
            session=MagicMock(spec=Session),
            device_manager=MagicMock(spec=IDeviceManager),
            session_create=test_session_create,
        )

        assert result is not None
        assert len(result) == 3
        assert isinstance(result[0], BuildPublic)
        assert isinstance(result[1], SessionTestPlanPublic)
        assert isinstance(result[2], DeviceWithStatus)

        mock_build_public_validate.assert_called_once_with(mock_read_build.return_value)
        mock_plan_public_validate.assert_called_once_with(
            mock_read_test_plan.return_value
        )

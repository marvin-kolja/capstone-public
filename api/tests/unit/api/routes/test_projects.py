import uuid
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from api.models import Build, Xctestrun


def test_list_available_tests_no_build(client):
    """
    GIVEN: A client

    WHEN: A request is made to get available tests for a build that does not exist

    THEN: It should return a 404 response
    """
    with patch("api.services.project_service.read_build") as mock_read_build:
        mock_read_build.return_value = None

        r = client.get(
            f"/projects/{uuid.uuid4()}/builds/{uuid.uuid4()}/available-tests"
        )

        assert r.status_code == 404
        assert r.json() == {"code": 404, "detail": "Build not found"}


@pytest.mark.parametrize(
    "status",
    ["failed", "running", "pending"],
)
@pytest.mark.parametrize(
    "xctestrun",
    [None, MagicMock(spec=Xctestrun)],
)
def test_list_available_tests_build_not_finished(client, status, xctestrun):
    """
    GIVEN: A client

    WHEN: A request is made to get available tests for a build that is not finished

    THEN: It should return a 400 response
    """
    with patch("api.services.project_service.read_build") as mock_read_build:
        mock_read_build.return_value = MagicMock(
            spec=Build, status="running", xctestrun=xctestrun
        )

        r = client.get(
            f"/projects/{uuid.uuid4()}/builds/{uuid.uuid4()}/available-tests"
        )

        assert r.status_code == 400
        assert r.json() == {"code": 400, "detail": "Build is not finished"}


def test_list_available_tests_device_not_connected(client):
    """
    GIVEN: A client

    WHEN: A request is made to get available tests for a build with a device that is not connected

    THEN: It should return a 400 response
    """
    with patch("api.services.project_service.read_build") as mock_read_build:
        mock_read_build.return_value = MagicMock(
            spec=Build, status="success", xctestrun=MagicMock(spec=Xctestrun)
        )

        with patch(
            "api.services.device_service.get_device_by_id"
        ) as mock_get_device_by_id:
            mock_get_device_by_id.return_value = None

            r = client.get(
                f"/projects/{uuid.uuid4()}/builds/{uuid.uuid4()}/available-tests"
            )

            assert r.status_code == 400
            assert r.json() == {"code": 400, "detail": "Device is not connected"}


def test_list_available_tests_success(client, mock_db_session_dependencies):
    """
    GIVEN: A client

    WHEN: A request is made to get available tests for a build that is successful

    THEN: It should return a 200 response
    AND: It should return the enabled/available tests returned from the service
    """
    with patch("api.services.project_service.read_build") as mock_read_build:
        db_build_mock = MagicMock(
            spec=Build, status="success", xctestrun=MagicMock(spec=Xctestrun)
        )
        xc_test_cases_mock = PropertyMock()
        type(db_build_mock).xc_test_cases = xc_test_cases_mock

        mock_read_build.return_value = db_build_mock

        with patch(
            "api.services.device_service.get_device_by_id"
        ) as mock_get_device_by_id:
            mock_get_device_by_id.return_value = MagicMock(connected=True)

            with patch(
                "api.services.project_service.list_available_tests"
            ) as mock_list_available_tests:
                mock_list_available_tests.return_value = ["test1", "test2"]

                r = client.get(
                    f"/projects/{uuid.uuid4()}/builds/{uuid.uuid4()}/available-tests"
                )

                assert r.status_code == 200
                assert r.json() == ["test1", "test2"]

                xc_test_cases_mock.assert_called_once_with(["test1", "test2"])

                assert mock_db_session_dependencies.add.call_count == 1
                assert mock_db_session_dependencies.commit.call_count == 1

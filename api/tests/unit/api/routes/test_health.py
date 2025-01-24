from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from sqlmodel import Session

from api.depends import get_db
from api.main import app


@pytest.fixture
def mock_db_session_dependencies():
    mock_db_session = MagicMock(spec=Session)

    async def override_db_session():
        return mock_db_session

    app.dependency_overrides[get_db] = override_db_session

    yield mock_db_session

    app.dependency_overrides = {}


@pytest.mark.parametrize(
    "db_status, tunnel_connect_status, expected_server_status",
    [
        ("ok", "ok", "ok"),
        ("unavailable", "ok", "unhealthy"),
        ("ok", "unavailable", "unhealthy"),
        ("unavailable", "unavailable", "unhealthy"),
    ],
)
def test_health_check(
    client,
    mock_db_session_dependencies,
    db_status,
    tunnel_connect_status,
    expected_server_status,
):

    with patch("api.routes.health.get_tunnel_client") as mock_get_tunnel_client:
        tunnel_client_mock = MagicMock()
        mock_get_tunnel_client.return_value.__enter__.return_value = tunnel_client_mock

        if tunnel_connect_status == "ok":
            tunnel_client_mock.get_tunnel.side_effect = AsyncMock(return_value=None)
        else:
            tunnel_client_mock.get_tunnel.side_effect = AsyncMock(side_effect=Exception)

        if db_status == "ok":
            mock_db_session_dependencies.exec.return_value.first.side_effect = None
        else:
            mock_db_session_dependencies.exec.return_value.first.side_effect = Exception

        response = client.get("/health")

        assert response.status_code == 200, response.text
        assert response.json() == {
            "status": expected_server_status,
            "db": db_status,
            "tunnel_connect": tunnel_connect_status,
        }

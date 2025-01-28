from unittest.mock import patch, MagicMock, AsyncMock

import pytest


@pytest.mark.parametrize(
    "db_status, tunnel_connect_status, expected_server_status",
    [
        ("ok", "ok", "ok"),
        ("unavailable", "ok", "unhealthy"),
        ("ok", "unavailable", "unhealthy"),
        ("unavailable", "unavailable", "unhealthy"),
    ],
)
@pytest.mark.asyncio
async def test_health_check(
    async_client,
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
            mock_db_session_dependencies.execute.side_effect = None
        else:
            mock_db_session_dependencies.execute.side_effect = Exception

        response = await async_client.get("/health")

        assert response.status_code == 200, response.text
        assert response.json() == {
            "status": expected_server_status,
            "db": db_status,
            "tunnel_connect": tunnel_connect_status,
        }

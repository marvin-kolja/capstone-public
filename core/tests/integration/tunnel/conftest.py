import logging
from datetime import timedelta

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
async def tunnel_server(port):
    from core.tunnel.server import get_tunnel_server

    server = get_tunnel_server()
    await server.serve(port=port)
    yield server
    server.stop()
    await server.await_close()


@pytest.fixture
def server(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def tunnel_client(port):
    from core.tunnel.client import get_tunnel_client

    with get_tunnel_client(port=port, timeout=timedelta(seconds=4)) as client:
        yield client

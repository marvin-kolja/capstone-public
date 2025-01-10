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
    yield request.getfixturevalue(request.param)


@pytest.fixture
def tunnel_client(request):
    """
    Instead of using the port fixture, we can determine the port dynamically based on the fixtures in the request.

    Some integration tests use the function scoped `tunnel_server` fixture and module scoped `tunnel_server_subprocess`
    fixture. The problem is that the `tunnel_server_subprocess` fixture is module wide and cannot use the same port as
    the `tunnel_server` fixture. Thus, we need to determine the port dynamically based on the fixtures in the request.

    If this fixture is used without the `tunnel_server` or `tunnel_server_subprocess` fixtures, it will default to the
    `port` fixture.
    """
    from core.tunnel.client import get_tunnel_client

    _port = None

    if "tunnel_server_subprocess" in request.fixturenames:
        _port = request.getfixturevalue("tunnel_server_subprocess_port")
    elif "tunnel_server" in request.fixturenames:
        _port = request.getfixturevalue("port")
    else:
        _port = request.getfixturevalue("port")

    with get_tunnel_client(port=_port, timeout=timedelta(seconds=2)) as client:
        yield client

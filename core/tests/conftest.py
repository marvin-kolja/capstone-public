import pytest

from core.socket import ClientSocket, ServerSocket


def pytest_runtest_setup(item):
    import os

    if "requires_sudo" in item.keywords and os.geteuid() != 0:
        pytest.skip("Test requires sudo")

@pytest.fixture
def port():
    # max user-defined port
    # https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml
    return 49151


@pytest.fixture
async def client_socket(port) -> ClientSocket:
    with ClientSocket(port=port) as client:
        yield client


@pytest.fixture
async def server_socket(port) -> ServerSocket:
    with ServerSocket(port=port) as server:
        yield server

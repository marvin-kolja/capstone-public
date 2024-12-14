import pytest

from core.async_socket import ClientSocket, ServerSocket


def pytest_addoption(parser):
    parser.addoption(
        '--device', action='store_true', default=False, help='Run tests that require a real device',
    )


def pytest_runtest_setup(item):
    import os

    if "requires_sudo" in item.keywords and os.geteuid() != 0:
        pytest.skip("Test requires sudo")

    if "real_device" in item.keywords and not item.config.getoption("--device"):
        pytest.skip("Test requires a real device. Use --device to run")


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


@pytest.fixture(scope="session")
def fake_udid():
    return "FAKE-UDID"


@pytest.fixture(scope="session")
def device_udid():
    """
    A fixture that returns an actual UDID of a connected device.
    """
    from pymobiledevice3.usbmux import list_devices

    udid = None
    for device in list_devices(usbmux_address=None):
        udid = device.serial
        break

    if udid:
        return udid

    raise pytest.exit("Failed to find a real device UDID", returncode=2)


@pytest.fixture(scope="function")
async def tunnel_connect():
    """
    A fixture that returns a `TunnelConnect` instance and cleans up after the test.
    """
    from core.tunnel.tunnel_connect import TunnelConnect

    tunnel_connect = TunnelConnect()
    yield tunnel_connect
    await tunnel_connect.close()

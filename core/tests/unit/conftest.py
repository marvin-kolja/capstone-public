import asyncio
import os
import pathlib
from datetime import timedelta
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

import pytest
import zmq
import zmq.asyncio
from pymobiledevice3.lockdown import UsbmuxLockdownClient
from pymobiledevice3.remote.common import TunnelProtocol
from pymobiledevice3.remote.tunnel_service import (
    TunnelResult as pymobiledevice3TunnelResult,
)
import pymobiledevice3.exceptions as pmd3_exceptions

from core.async_socket import ClientSocket
from core.codec.socket_json_codec import SocketMessageJSONCodec
from core.device.i_device import IDevice
from core.xc.xctest import Xctest
from core.tunnel.client import get_tunnel_client
from core.tunnel.interface import TunnelResult


@pytest.fixture
def magic_mock_socket():
    return MagicMock()


@pytest.fixture
def mock_zmq_context(request, magic_mock_socket):
    with patch("zmq.asyncio.Context") as mock_ctx:
        mock_socket = magic_mock_socket
        mock_socket.fileno.return_value = 1
        mock_ctx.return_value.socket.return_value = mock_socket

        mock_socket.connect.return_value = None
        mock_socket.setsockopt.return_value = None
        mock_socket.close.return_value = None

        mock_socket.send_multipart = AsyncMock(return_value=None)

        mock_socket.recv_multipart = AsyncMock(return_value=request.param)

        yield mock_socket


@pytest.fixture
def mock_zmq_poller(magic_mock_socket):
    with patch("zmq.asyncio.Poller") as mock_poll:
        mock_poller_instance = MagicMock()
        mock_poller_instance.poll = AsyncMock(
            return_value=[(magic_mock_socket, zmq.POLLIN)]
        )
        mock_poll.return_value = mock_poller_instance

        yield mock_poller_instance


@pytest.fixture(scope="function")
def spy_zmq_socket_close(mocker):
    return mocker.spy(zmq.asyncio.Socket, "close")


@pytest.fixture(scope="function")
def spy_zmq_context_term(mocker):
    return mocker.spy(zmq.asyncio.Context, "term")


@pytest.fixture(scope="function")
def spy_socket_decode(mocker):
    return mocker.spy(SocketMessageJSONCodec, "decode_message")


@pytest.fixture(scope="function")
def spy_socket_encode(mocker):
    return mocker.spy(SocketMessageJSONCodec, "encode_message")


@pytest.fixture
def mocked_pymd3_tunnel_result(mocker):
    """
    A mocked `pymobiledevice3` TunnelResult` that can be used to simulate a tunnel result.
    """
    client = mocker.MagicMock()

    async def wait_closed():
        while not getattr(client, "closed", False):
            await asyncio.sleep(0.1)

    client.closed = False
    client.close = mocker.AsyncMock(side_effect=lambda: setattr(client, "closed", True))
    client.wait_closed = mocker.AsyncMock(side_effect=wait_closed)

    return pymobiledevice3TunnelResult(
        address="127.0.0.1",
        port=1234,
        protocol=TunnelProtocol.TCP,
        interface="",
        client=client,
    )


@pytest.fixture
def fake_tunnel_result(mocked_pymd3_tunnel_result):
    """
    A fake tunnel result that can be used to simulate a tunnel result.
    """
    tunnel_result = TunnelResult(
        address=mocked_pymd3_tunnel_result.address,
        port=mocked_pymd3_tunnel_result.port,
        protocol=TunnelProtocol.TCP,
    )
    return tunnel_result


@pytest.fixture
def mocked_client_socket():
    with patch("core.tunnel.client.ClientSocket") as mock_socket:
        mock_instance = AsyncMock(spec=ClientSocket)
        mock_socket.return_value.__enter__.return_value = mock_instance
        mock_socket.return_value.__exit__.return_value = None
        yield mock_instance


@pytest.fixture
def tunnel_client_with_mocked_socket(mocked_client_socket, port):
    """
    A fixture to create a `TunnelClient` instance with a mocked `ClientSocket`.
    """
    with get_tunnel_client(port=port, timeout=timedelta(seconds=1)) as client:
        yield client


@pytest.fixture(scope="session")
def example_xctestrun_path():
    """
    Fixture to return path to real xctestrun file which was generated by Xcode 16.0 (16A242d).
    """
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    return pathlib.Path(current_dir, "..", "test_data", "Example.xctestrun")


@pytest.fixture()
def example_xctestrun(example_xctestrun_path):
    """
    Fixture to parse the `example_xctestrun_path` and return the parsed xctestrun.
    """
    return Xctest.parse_xctestrun(example_xctestrun_path.absolute().as_posix())


@pytest.fixture(scope="session")
def example_info_plist_path():
    """
    Fixture to return path to real Info.plist file which was generated by Xcode 16.0 (16A242d).
    """
    current_dir = pathlib.Path(os.path.abspath(__file__)).parent
    return pathlib.Path(current_dir, "..", "test_data", "Example-Info.plist")


@pytest.fixture()
def mock_usbmux_lockdown_client(
    paired, developer_mode_enabled, product_version, fake_udid
) -> UsbmuxLockdownClient:
    mock_instance = MagicMock(spec=UsbmuxLockdownClient)
    mock_instance.product_version = product_version
    mock_instance.paired = paired
    if not paired:
        type(mock_instance).developer_mode_status = PropertyMock(
            side_effect=pmd3_exceptions.NotPairedError()
        )
    else:
        mock_instance.developer_mode_status = developer_mode_enabled
    mock_instance.udid = fake_udid
    return mock_instance


@pytest.fixture()
def i_device_mocked_lockdown(mock_usbmux_lockdown_client):
    return IDevice(lockdown_client=mock_usbmux_lockdown_client)

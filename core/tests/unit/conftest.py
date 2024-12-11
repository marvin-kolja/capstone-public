from unittest.mock import MagicMock, patch, AsyncMock

import pytest
import zmq
import zmq.asyncio

from core.codec.socket_json_codec import SocketMessageJSONCodec


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

        mock_socket.recv_multipart = AsyncMock(
            return_value=request.param
        )

        yield mock_socket


@pytest.fixture
def mock_zmq_poller(magic_mock_socket):
    with patch("zmq.asyncio.Poller") as mock_poll:
        mock_poller_instance = MagicMock()
        mock_poller_instance.poll = AsyncMock(return_value=[(magic_mock_socket, zmq.POLLIN)])
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

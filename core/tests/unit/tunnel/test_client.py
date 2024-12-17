from datetime import timedelta
from unittest.mock import patch, AsyncMock

import pytest
from pymobiledevice3.exceptions import DeviceNotFoundError, NoDeviceConnectedError

from core.codec.socket_json_codec import ClientRequest, ErrorResponse, SuccessResponse
from core.exceptions.tunnel_connect import TunnelAlreadyExistsError
from core.async_socket import ClientSocket
from core.tunnel.client import get_error_from_context, Client, get_tunnel_client
from core.tunnel.server_exceptions import ServerErrorCode, TunnelServerErrorCode, InternalServerError, \
    MalformedRequestError, NotFoundError

exception_map = [
    (ServerErrorCode.INTERNAL, InternalServerError),
    (ServerErrorCode.MALFORMED_REQUEST, MalformedRequestError),
    (ServerErrorCode.NOT_FOUND, NotFoundError),
    (TunnelServerErrorCode.DEVICE_NOT_FOUND, DeviceNotFoundError),
    (TunnelServerErrorCode.NO_DEVICE_CONNECTED, NoDeviceConnectedError),
    (TunnelServerErrorCode.TUNNEL_ALREADY_EXISTS, TunnelAlreadyExistsError),
]


@pytest.fixture(
    scope="session",
    params=exception_map,
)
def error_code_and_exception(request):
    return request.param


@pytest.fixture(scope="session")
def unknown_error_codes():
    error_codes = []
    known_error_codes = [code for code, _ in exception_map]
    max_known_error_code = max(known_error_codes)

    for i in range(max_known_error_code + 1):
        if i not in known_error_codes:
            error_codes.append(i)

    return error_codes


@pytest.fixture
def mocked_client_socket():
    with patch('core.tunnel.client.ClientSocket') as mock_socket:
        mock_instance = AsyncMock(spec=ClientSocket)
        mock_socket.return_value.__enter__.return_value = mock_instance
        mock_socket.return_value.__exit__.return_value = None
        yield mock_instance


class TestGetErrorFromContext:

    def test_known_error_codes(self, error_code_and_exception):
        """
        GIVEN: An error code
        AND: The expected exception for that error code.

        WHEN: `get_error_from_context` is called.

        THEN: The expected exception is returned.
        """
        error_code, expected_exception = error_code_and_exception
        request = ClientRequest(action='dummy', data={'udid': 'dummy'})
        error_response = ErrorResponse(error_code=error_code.value)

        exception = get_error_from_context(request, error_response)

        assert isinstance(exception, expected_exception)

    def test_unknown_error_code(self, unknown_error_codes):
        """
        GIVEN: A list of unknown error codes.

        WHEN: `get_error_from_context` is called with an error response with an unknown error code.

        THEN: A ValueError is raised.
        """
        request = ClientRequest(action='dummy')
        for unknown_error_code in unknown_error_codes:
            error_response = ErrorResponse(error_code=unknown_error_code)
            with pytest.raises(ValueError):
                get_error_from_context(request, error_response)


class TestClient:

    def test_context_manager(self, mocked_client_socket):
        """
        GIVEN: A `Client` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client is used as a context manager.

        THEN: The client should establish a connection with the server.
        """
        with Client(port=1234, timeout=timedelta(seconds=5)) as client:
            assert client._socket is mocked_client_socket

    def test_no_context_manager(self):
        """
        GIVEN: A `Client` instance.

        WHEN: The client is not used as a context manager.

        THEN: The client should not establish a connection with the server.
        """
        client = Client(port=1234, timeout=timedelta(seconds=5))

        assert client._socket is None

    @pytest.mark.asyncio
    async def test_call_server_success(self, port, mocked_client_socket):
        """
        GIVEN: A `Client` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client calls the server with a valid action and parameters.

        THEN: The client should receive a success response from the server.
        """
        expected_result = {'key': 'value'}
        # Simulate a successful response from the server
        mocked_client_socket.receive.return_value = SuccessResponse(data=expected_result)

        with Client(port=port, timeout=timedelta(seconds=5)) as client:
            result = await client._call_server('some_action', param='test')

        assert result == expected_result
        mocked_client_socket.send.assert_awaited_once()
        mocked_client_socket.receive.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_server_error_response(self, port, mocked_client_socket):
        """
        GIVEN: A `Client` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client calls the server.
        AND: The server responds with an error.

        THEN: The client should receive an error response from the server.
        """
        # The server will respond with a NOT_FOUND error
        mocked_client_socket.receive.return_value = ErrorResponse(error_code=ServerErrorCode.NOT_FOUND.value)
        with Client(port=port, timeout=timedelta(seconds=5)) as client:
            print(client._socket)
            with pytest.raises(NotFoundError):
                await client._call_server('invalid_action', param='test')


class TestTunnelClient:
    @pytest.fixture
    def tunnel_client_with_mocked_socket(self, mocked_client_socket, port):
        """
        A fixture to create a `TunnelClient` instance with a mocked `ClientSocket`.
        """
        with get_tunnel_client(port=port, timeout=timedelta(seconds=1)) as client:
            yield client

    @pytest.mark.asyncio
    async def test_start_tunnel_success(self, tunnel_client_with_mocked_socket, fake_tunnel_result, fake_udid):
        """
        GIVEN: A `TunnelClient` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client tries to start a tunnel.
        AND: The server responds with a tunnel result.

        THEN: The called method should return the tunnel result as is.
        """
        # Simulate a successful tunnel creation
        tunnel_client_with_mocked_socket._socket.receive.return_value = SuccessResponse(
            data=fake_tunnel_result.model_dump(mode='json'))

        result = await tunnel_client_with_mocked_socket.start_tunnel(fake_udid)
        assert result == fake_tunnel_result

    @pytest.mark.asyncio
    async def test_start_tunnel_tunnel_already_exists(self, tunnel_client_with_mocked_socket, fake_udid):
        """
        GIVEN: A `TunnelClient` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client tries to start a tunnel.
        AND: The server responds with a TUNNEL_ALREADY_EXISTS error.

        THEN: The called method should raise TunnelAlreadyExistsError.
        """
        # Simulate a tunnel already exists error
        tunnel_client_with_mocked_socket._socket.receive.return_value = ErrorResponse(
            error_code=TunnelServerErrorCode.TUNNEL_ALREADY_EXISTS.value
        )
        with pytest.raises(TunnelAlreadyExistsError):
            await tunnel_client_with_mocked_socket.start_tunnel(fake_udid)

    @pytest.mark.asyncio
    async def test_stop_tunnel_success(self, tunnel_client_with_mocked_socket, fake_udid):
        """
        GIVEN: A `TunnelClient` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client tries to stop a tunnel.
        AND: The server responds with a success response.

        THEN: The called method should return None.
        """
        # Simulate a successful server response for stopping a tunnel
        tunnel_client_with_mocked_socket._socket.receive.return_value = SuccessResponse()

        result = await tunnel_client_with_mocked_socket.stop_tunnel(fake_udid)

        assert result is None

    @pytest.mark.asyncio
    async def test_stop_tunnel_device_not_found(self, tunnel_client_with_mocked_socket, fake_udid):
        """
        GIVEN: A `TunnelClient` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client tries to stop a tunnel.
        AND: The server responds with a DEVICE_NOT_FOUND error.

        THEN: The called method should raise a DeviceNotFoundError
        """
        # Simulate a device not found error
        tunnel_client_with_mocked_socket._socket.receive.return_value = ErrorResponse(
            error_code=TunnelServerErrorCode.DEVICE_NOT_FOUND.value
        )
        with pytest.raises(DeviceNotFoundError):
            await tunnel_client_with_mocked_socket.stop_tunnel(fake_udid)

    @pytest.mark.asyncio
    async def test_get_tunnel_success(self, tunnel_client_with_mocked_socket, fake_tunnel_result, fake_udid):
        """
        GIVEN: A `TunnelClient` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client tries to get a tunnel.
        AND: The server responds with a tunnel result.

        THEN: The called method should return the tunnel result as is.
        """
        # Simulate a successful tunnel retrieval
        tunnel_client_with_mocked_socket._socket.receive.return_value = SuccessResponse(
            data=fake_tunnel_result.model_dump(mode='json'))

        result = await tunnel_client_with_mocked_socket.get_tunnel(fake_udid)

        assert result == fake_tunnel_result

    @pytest.mark.asyncio
    async def test_get_tunnel_not_found(self, tunnel_client_with_mocked_socket, fake_udid):
        """
        GIVEN: A `TunnelClient` instance.
        AND: A mocked `ClientSocket` instance.

        WHEN: The client tries to get a tunnel.
        AND: The server responds with a NOT_FOUND error.

        THEN: The called method should return None.
        """
        # Simulate a tunnel not found error
        tunnel_client_with_mocked_socket._socket.receive.return_value = ErrorResponse(
            error_code=ServerErrorCode.NOT_FOUND.value
        )

        assert await tunnel_client_with_mocked_socket.get_tunnel(fake_udid) is None

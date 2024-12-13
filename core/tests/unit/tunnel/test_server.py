import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, IPvAnyAddress
from pymobiledevice3.exceptions import DeviceNotFoundError

from core.codec.socket_json_codec import SuccessResponse, ClientRequest, ErrorResponse
from core.socket import ServerSocket
from core.tunnel.server import server_method, Server, ServerMethodHandler, check_server_method, bind_arguments, \
    TunnelConnectService
from core.tunnel.server_exceptions import MalformedRequestError, NotFoundError, TunnelServerError, \
    TunnelServerErrorCode, InternalServerError, ServerErrorCode
from core.tunnel.tunnel_connect import TunnelConnect


def test_check_server_method():
    """
    GIVEN: A method decorated with the `server_method` decorator.

    WHEN: Checking if the method is a server method.

    THEN: The function should return True.
    """

    class DummyHandler(ServerMethodHandler):
        @server_method
        def dummy_method(self):
            pass

    assert check_server_method(DummyHandler().dummy_method)


def test_check_server_method_with_invalid_type():
    """
    GIVEN: A function that is not a method instance.

    WHEN: Checking if the method is a server method.

    THEN: The function should raise a TypeError.
    """
    with pytest.raises(TypeError):
        check_server_method(lambda x: x)  # not a method instance


def test_check_server_method_without_decorator():
    """
    GIVEN: A method not decorated with the `server_method` decorator.

    WHEN: Checking if the method is a server method.

    THEN: The function should raise an AttributeError.
    """

    class Dummy:
        def method(self, x):
            return x

    d = Dummy()
    with pytest.raises(AttributeError):
        check_server_method(d.method)


def test_bind_arguments_valid():
    """
    GIVEN: A method decorated with the `server_method` decorator.
    AND: A dictionary of arguments to bind to the method.

    WHEN: Binding arguments to the method.

    THEN: The function should return the correct arguments.
    """
    data = {'arg1': 'test', 'arg2': 1}

    @server_method
    async def dummy_method(arg1: str, arg2: int = 2):
        pass

    arguments = bind_arguments(dummy_method, data)

    assert arguments == data


def test_bind_arguments_invalid():
    """
    GIVEN: A method decorated with the `server_method` decorator.
    AND: A dictionary of incorrect arguments to bind to the method.

    WHEN: Binding arguments to the method.

    THEN: The function should raise a TypeError.
    """
    data = {'arg3': 2, 'arg1': 'test'}

    @server_method
    async def dummy_method(arg1: str, arg2: int):
        pass

    with pytest.raises(TypeError):
        bind_arguments(dummy_method, data)


class TestTunnelConnectService:
    @pytest.mark.asyncio
    async def test_start_tunnel_valid(self, fake_tunnel_result, fake_udid):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `start_tunnel` method with a UDID.

        THEN: The method should return a `TunnelResult` instance.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        mock_tunnel_connect.start_tunnel.return_value = fake_tunnel_result
        service = TunnelConnectService(mock_tunnel_connect)

        result = await service.start_tunnel(fake_udid)
        assert result == fake_tunnel_result
        mock_tunnel_connect.start_tunnel.assert_awaited_once_with(fake_udid)

    @pytest.mark.asyncio
    async def test_start_tunnel_invalid_udid_type(self):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `start_tunnel` method with an integer UDID.

        THEN: The method should raise a `MalformedRequestError`.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        service = TunnelConnectService(mock_tunnel_connect)

        with pytest.raises(MalformedRequestError):
            await service.start_tunnel(123)

    @pytest.mark.asyncio
    async def test_start_tunnel_empty_udid(self):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `start_tunnel` method with an empty string.

        THEN: The method should raise a `MalformedRequestError`.
        """

        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        service = TunnelConnectService(mock_tunnel_connect)

        with pytest.raises(MalformedRequestError):
            await service.start_tunnel("")

    @pytest.mark.asyncio
    async def test_start_tunnel_device_not_found(self, fake_udid):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `start_tunnel` method
        AND: The device is not found.

        THEN: The method should raise a `TunnelServerError` with the correct error code.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        mock_tunnel_connect.start_tunnel.side_effect = DeviceNotFoundError(fake_udid)
        service = TunnelConnectService(mock_tunnel_connect)

        with pytest.raises(TunnelServerError) as exc_info:
            await service.start_tunnel(fake_udid)
        assert exc_info.value.error_code == TunnelServerErrorCode.DEVICE_NOT_FOUND.value

    @pytest.mark.asyncio
    async def test_stop_tunnel_valid(self, fake_udid):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `stop_tunnel` method with a UDID.

        THEN: The method should call the `TunnelConnect.stop_tunnel` method with the UDID.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        service = TunnelConnectService(mock_tunnel_connect)

        await service.stop_tunnel(fake_udid)
        mock_tunnel_connect.stop_tunnel.assert_awaited_once_with(fake_udid)

    @pytest.mark.asyncio
    async def test_stop_tunnel_malformed(self, fake_udid):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `stop_tunnel` method with an integer UDID.

        THEN: The method should raise a `MalformedRequestError`.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        service = TunnelConnectService(mock_tunnel_connect)

        with pytest.raises(MalformedRequestError):
            await service.stop_tunnel(123)

    @pytest.mark.asyncio
    async def test_get_tunnel_valid(self, fake_udid, fake_tunnel_result):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `get_tunnel` method with a UDID.

        THEN: The method should return a `TunnelResult` instance.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        mock_tunnel_connect.get_tunnel.return_value = fake_tunnel_result
        service = TunnelConnectService(mock_tunnel_connect)

        result = service.get_tunnel(fake_udid)
        assert result is fake_tunnel_result
        mock_tunnel_connect.get_tunnel.assert_called_once_with(fake_udid)

    @pytest.mark.asyncio
    async def test_get_tunnel_not_found(self, fake_udid):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `get_tunnel` method with a UDID.

        THEN: The method should raise a `NotFoundError`.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        mock_tunnel_connect.get_tunnel.return_value = None
        service = TunnelConnectService(mock_tunnel_connect)

        with pytest.raises(NotFoundError):
            service.get_tunnel(fake_udid)

    @pytest.mark.asyncio
    async def test_get_tunnel_malformed(self):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `get_tunnel` method with an integer UDID.

        THEN: The method should raise a `MalformedRequestError`.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        service = TunnelConnectService(mock_tunnel_connect)

        with pytest.raises(MalformedRequestError):
            service.get_tunnel(123)

    @pytest.mark.asyncio
    async def test_service_cleanup(self):
        """
        GIVEN: A TunnelConnectService instance with a mocked `TunnelConnect` instance.

        WHEN: Calling the `cleanup` method.

        THEN: The method should call the `TunnelConnect.close` method.
        """
        mock_tunnel_connect = AsyncMock(spec=TunnelConnect)
        service = TunnelConnectService(mock_tunnel_connect)
        await service.cleanup()
        mock_tunnel_connect.close.assert_awaited_once()


class TestServer:
    def test_init_invalid_service(self):
        """
        GIVEN: And invalid service to bind to the server.

        WHEN: Creating a `Server` instance.

        THEN: The constructor should raise a ValueError.
        """
        with pytest.raises(ValueError):
            Server(service=None)

        class NotAHandler:
            pass

        with pytest.raises(ValueError):
            Server(service=NotAHandler())

    @pytest.mark.asyncio
    async def test_get_method_valid(self):
        """
        GIVEN: A `Server` instance with a valid dummy service.

        WHEN: Getting a method from the service.

        THEN: The method should be returned.
        """

        class DummyService(ServerMethodHandler):
            @server_method
            async def hello(self):
                return "world"

        server = Server(DummyService())
        m = server._get_method("hello")
        assert m is not None

    @pytest.mark.asyncio
    async def test_get_method_not_found(self):
        """
        GIVEN: A `Server` instance with a valid dummy service.

        WHEN: Getting a method that does not exist.

        THEN: The method should raise a `NotFoundError`.
        """

        class DummyService(ServerMethodHandler):
            pass

        server = Server(DummyService())
        with pytest.raises(NotFoundError):
            server._get_method("missing_method")

    @pytest.mark.asyncio
    async def test_bind_arguments_malformed(self):
        """
        GIVEN: A `Server` instance with a valid dummy service.

        WHEN: Binding arguments to a method with missing arguments.

        THEN: The method should raise a `MalformedRequestError`.
        """

        class DummyService(ServerMethodHandler):
            @server_method
            def add(self, x, y):
                return x + y

        s = Server(DummyService())
        method = s._get_method("add")
        with pytest.raises(MalformedRequestError):
            s._bind_arguments(method, {'x': 1})

    @pytest.mark.asyncio
    async def test_call_method_sync(self):
        """
        GIVEN: A `Server` instance with a valid dummy service
        AND: A method that returns a synchronous result.

        WHEN: Calling the method.

        THEN: The method should return the correct result.
        """
        input_data = {'name': 'Alice'}
        expected_result = "Hello Alice"

        class DummyService(ServerMethodHandler):
            @server_method
            def greet(self, name: str):
                return f"Hello {name}"

        s = Server(DummyService())
        method = s._get_method("greet")
        result = await s._call_method(method, input_data)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_call_method_async(self):
        """
        GIVEN: A `Server` instance with a valid dummy service
        AND: A method that returns an asynchronous result.

        WHEN: Calling the method.

        THEN: The method should return the correct result.
        """
        input_data = {'name': 'Alice'}
        expected_result = "Hello Alice"

        class DummyService(ServerMethodHandler):
            @server_method
            async def greet_async(self, name: str):
                await asyncio.sleep(0.01)
                return f"Hello {name}"

        s = Server(DummyService())
        method = s._get_method("greet_async")
        result = await s._call_method(method, input_data)
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_construct_response_from_result_none(self):
        """
        GIVEN: The result of a method is `None`.

        WHEN: Constructing a response from the result.

        THEN: The method should return a `SuccessResponse` with no data.
        """
        response = Server._construct_response_from_result(None)
        assert isinstance(response, SuccessResponse)
        assert response.data is None

    @pytest.mark.asyncio
    async def test_construct_response_from_result_pydantic(self):
        """
        GIVEN: The result of a method is a Pydantic model.

        WHEN: Constructing a response from the result.

        THEN: The method should return a `SuccessResponse` with the correct data.
        """

        class FakeBaseModel(BaseModel):
            foo: str
            ip: IPvAnyAddress

        data = {"foo": "bar", "ip": "127.0.0.1"}

        resp = Server._construct_response_from_result(FakeBaseModel(**data))
        assert isinstance(resp, SuccessResponse)
        assert resp.data == data

    @pytest.mark.asyncio
    async def test_construct_response_from_result_dict(self):
        """
        GIVEN: The result of a method is a dictionary.

        WHEN: Constructing a response from the result.

        THEN: The method should return a `SuccessResponse` with the correct data.
        """
        data = {"key": "value"}

        resp = Server._construct_response_from_result(data)
        assert isinstance(resp, SuccessResponse)
        assert resp.data == data

    @pytest.mark.asyncio
    async def test_construct_response_from_result_invalid(self):
        """
        GIVEN: The result of a method is not a valid type.

        WHEN: Constructing a response from the result.

        THEN: The method should raise an `InternalServerError`.
        """
        with pytest.raises(InternalServerError):
            Server._construct_response_from_result(12345)

    @pytest.mark.asyncio
    async def test_serve_fail(self, port):
        """
        GIVEN: A `Server` instance
        AND: A mocked service.
        AND: A mocked __server_task method.

        WHEN: Starting the server
        AND: The server fails to start.

        THEN: The server should raise an exception.
        """
        mock_service = MagicMock(spec=ServerMethodHandler)
        server = Server(mock_service)

        with patch.object(server, '_Server__server_task') as mock_server_task:
            mock_server_task.side_effect = Exception
            with pytest.raises(Exception):
                await server.serve(port=port)

    @pytest.mark.asyncio
    async def test_serve_and_stop(self, port):
        """
        GIVEN: A `Server` instance
        AND: A mocked service.
        AND: A mocked server socket.

        WHEN: Starting the server
        AND: Stopping the server.

        THEN: The server should create a task that is not done.
        AND: The server should stop the task and remove it.
        """
        mock_service = MagicMock(spec=ServerMethodHandler)
        server = Server(mock_service)

        with patch('core.socket.ServerSocket') as mock_socket:
            mock_instance = MagicMock()
            mock_socket.return_value.__enter__.return_value = mock_instance

            await server.serve(port=port)

            task = server._server_task
            assert not task.done()

            await server.stop()

            assert task.done()
            assert server._server_task is None

    @pytest.mark.asyncio
    async def test_process_incoming_request_valid(self, port):
        """
        GIVEN: A `Server` instance
        AND: A dummy service.
        AND: A mocked server socket.

        WHEN: Processing a valid incoming request.

        THEN: The server should respond with the correct data.
        """

        class DummyService(ServerMethodHandler):
            @server_method
            def hello(self, name: str):
                return {"hello": name}

        server = Server(DummyService())

        mocked_socket = AsyncMock(spec=ServerSocket)
        mocked_socket.receive.return_value = ClientRequest(action="hello", data={"name": "Alice"})
        mocked_socket.respond.return_value = None

        await server._process_incoming_request(mocked_socket)

        mocked_socket.respond.assert_awaited_once_with(SuccessResponse(data={"hello": "Alice"}))

    @pytest.mark.asyncio
    async def test_process_incoming_request_server_error(self, port):
        """
        GIVEN: A `Server` instance
        AND: A dummy service.
        AND: A mocked server socket.

        WHEN: Processing a valid incoming request.
        AND: The server raises some server error.

        THEN: The server should respond with an `ErrorResponse` with the correct error code.
        """

        class DummyService(ServerMethodHandler):
            @server_method
            def hello(self, name: str):
                raise MalformedRequestError()

        server = Server(DummyService())

        mocked_socket = AsyncMock(spec=ServerSocket)
        mocked_socket.receive.return_value = ClientRequest(action="hello", data={"name": "Alice"})
        mocked_socket.respond.return_value = None

        await server._process_incoming_request(mocked_socket)

        mocked_socket.respond.assert_awaited_once_with(
            ErrorResponse(error_code=ServerErrorCode.MALFORMED_REQUEST.value))

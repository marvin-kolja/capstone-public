import asyncio
import inspect
from abc import ABC
from datetime import timedelta

from types import MethodType
from typing import Optional, TypeVar, Generic

from pydantic import BaseModel
from pymobiledevice3.exceptions import DeviceNotFoundError, NoDeviceConnectedError

from core.codec.socket_json_codec import ServerSocketMessageJSONCodec, SuccessResponse, ErrorResponse
from core.exceptions.socket import InvalidSocketMessage
from core.exceptions.tunnel_connect import TunnelAlreadyExistsError
from core.socket import ServerSocket
from core.tunnel.interface import TunnelConnectInterface, TunnelResult
from core.tunnel.server_exceptions import MalformedRequestError, TunnelServerError, TunnelServerErrorCode, \
    NotFoundError, InternalServerError, CoreServerError, ServerErrorCode
from core.tunnel.tunnel_connect import TunnelConnect


def server_method(func):
    """
    Decorator to mark a method as a server method

    Inspired by https://github.com/aio-libs/aiozmq/blob/master/aiozmq/rpc/base.py#L79-L83

    """
    func.__server__ = {}
    func.__signature__ = inspect.signature(func)
    return func


def check_server_method(func) -> MethodType:
    if not isinstance(func, MethodType):
        raise TypeError
    if not hasattr(func, '__server__'):
        raise AttributeError
    if not hasattr(func, '__signature__'):
        raise AttributeError
    return func


def bind_arguments(method: MethodType, data: dict) -> dict:
    """
    Tries to bind the arguments to the method signature.

    :param method: The method to bind the arguments to.
    :param data: The data to bind to the method.

    :return: The bound arguments.

    :raises TypeError: If the data does not match the method signature.
    """
    signature = inspect.signature(method)
    bound_arguments = signature.bind(**data)
    return bound_arguments.arguments


class ServerMethodHandler(ABC):
    """
    An abstract class to handle server methods and cleanup.
    """

    def __getitem__(self, key):
        """
        Get an attribute by key.

        :param key: The name of the attribute.
        :return: The attribute if it exists

        :raises KeyError: If the attribute does not exist
        """
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError

    async def cleanup(self):
        """
        Cleanup any resources used by the handler.
        """
        pass


class TunnelConnectService(ServerMethodHandler, TunnelConnectInterface):
    """
    A class that uses the TunnelConnect class to provide a server interface to start, stop and get tunnels to devices.
    """

    def __init__(self, tunnel_connect: TunnelConnect):
        if tunnel_connect is None:
            raise ValueError("TunnelConnect cannot be None")
        self.tunnel_connect = tunnel_connect

    @server_method
    async def start_tunnel(self, udid: str) -> TunnelResult:
        """
        Start a tunnel to a device.

        :param udid: The UDID of the device to connect to.
        :return: The tunnel result.

        :raises TunnelServerError: If there is an error starting the tunnel.
        :raises MalformedRequestError: If the request is malformed.
        """
        if not isinstance(udid, str):
            raise MalformedRequestError()
        if not udid:
            raise MalformedRequestError()

        try:
            return await self.tunnel_connect.start_tunnel(udid)
        except DeviceNotFoundError:
            raise TunnelServerError(error_code=TunnelServerErrorCode.DEVICE_NOT_FOUND)
        except TunnelAlreadyExistsError:
            raise TunnelServerError(error_code=TunnelServerErrorCode.TUNNEL_ALREADY_EXISTS)
        except NoDeviceConnectedError:
            raise TunnelServerError(error_code=TunnelServerErrorCode.NO_DEVICE_CONNECTED)

    @server_method
    async def stop_tunnel(self, udid: str) -> None:
        """
        Stop the tunnel to a device.

        Does nothing if the tunnel does not exist.

        :param udid: The UDID of the device to disconnect from.

        :raises MalformedRequestError: If the request is malformed.
        """
        if not isinstance(udid, str):
            raise MalformedRequestError()
        if not udid:
            raise MalformedRequestError()

        await self.tunnel_connect.stop_tunnel(udid)

    @server_method
    def get_tunnel(self, udid: str) -> TunnelResult:
        """
        Get the tunnel to a device.

        :param udid: The UDID of the device to get the tunnel for.
        :return: The tunnel result

        :raises MalformedRequestError: If the request is malformed.
        :raises NotFoundError: If the tunnel does not exist
        """

        if not isinstance(udid, str):
            raise MalformedRequestError()
        if not udid:
            raise MalformedRequestError()

        tunnel = self.tunnel_connect.get_tunnel(udid)

        if tunnel is None:
            raise NotFoundError()

        return tunnel

    async def cleanup(self):
        """
        Close all tunnels and cleanup resources
        """
        await self.tunnel_connect.close()


SERVICE = TypeVar('SERVICE', bound=ServerMethodHandler)


class Server(Generic[SERVICE]):
    """
    A class to run a socket server that handles requests and responses using a ServerMethodHandler.

    Messages are encoded and decoded using the ServerSocketMessageJSONCodec.
    """

    def __init__(self, service: SERVICE):
        if service is None or not isinstance(service, ServerMethodHandler):
            raise ValueError("Invalid service")
        self._service: SERVICE = service
        self._server_task: Optional[asyncio.Task] = None

    async def __server_task(self, port: int):
        try:
            with ServerSocket(port=port, codec=ServerSocketMessageJSONCodec()) as server:
                while True:
                    await self._process_incoming_request(server)
        finally:
            await self._service.cleanup()

    async def _process_incoming_request(self, server: ServerSocket):
        try:
            request = await server.receive(timeout=timedelta(seconds=360))
        except TimeoutError as e:
            # TODO: better logging
            print(repr(e))
            return

        try:
            method = self._get_method(request.action)
            kwargs = self._bind_arguments(method, request.data)
            result = await self._call_method(method, kwargs)
            response = self._construct_response_from_result(result)
        except CoreServerError as e:
            # TODO: better logging
            print(repr(e))
            response = ErrorResponse(error_code=ServerErrorCode.INTERNAL.value)
        except Exception as e:
            # TODO: better logging
            print(f"Unexpected error: {repr(e)}")
            response = ErrorResponse(error_code=ServerErrorCode.INTERNAL.value)

        try:
            await server.respond(response)
        except InvalidSocketMessage as e:
            # TODO: better logging
            print(f"Failed to respond: {repr(e)}")
            await server.respond(ErrorResponse(error_code=ServerErrorCode.INTERNAL.value))

    def _get_method(self, method_name: str) -> MethodType:
        """
        :raises NotFoundError: If the method does not exist.
        """
        try:
            attribute = self._service[method_name]
            return check_server_method(attribute)
        except (KeyError, AttributeError, TypeError) as e:
            # TODO: better error handling
            print(repr(e))
            raise NotFoundError()

    @staticmethod
    def _bind_arguments(method: MethodType, data: dict) -> dict:
        """
        Bind the arguments to the method signature.

        :raises MalformedRequestError: if it fails to bind the arguments.
        """
        try:
            kwargs = bind_arguments(method, data)
        except TypeError as e:
            # TODO: better error handling
            print(repr(e))
            raise MalformedRequestError()

        return kwargs

    @staticmethod
    async def _call_method(method: MethodType, kwargs: dict):
        if asyncio.iscoroutinefunction(method):
            return await method(**kwargs)
        else:
            return method(**kwargs)

    @staticmethod
    def _construct_response_from_result(result) -> SuccessResponse:
        """
        Construct a response from the result of a service method.
        :param result: Can be a BaseModel, dict or None.
        :return: A SuccessResponse with the data from the result.

        :raises InternalServerError: If result is not a BaseModel, dict, or None.
        """
        if result is None:
            return SuccessResponse()
        if isinstance(result, BaseModel):
            return SuccessResponse(data=result.model_dump(mode='json'))
        if isinstance(result, dict):
            return SuccessResponse(data=result)
        else:
            # TODO: better error handling
            print(f"Invalid response data: {result}")
            raise InternalServerError()

    async def serve(self, port: int):
        """
        Start a server task

        Will wait for a short time to check if the server closes immediately.

        If the server closes immediately, the server is awaited which may raise an exception.
        """
        self._server_task = asyncio.create_task(self.__server_task(port=port))
        await asyncio.sleep(0.1)
        if self._server_task.done():
            await self.await_close()

    async def await_close(self):
        """
        Await the server task to close and cleanup the service.

        :raises: Any exception that caused the server task to close.
        """
        try:
            await self._server_task
            self._server_task.result()
        finally:
            await self._service.cleanup()

    async def stop(self):
        """
        Cancels the server task if it exists and waits for it to close.
        """
        raise NotImplementedError()


def get_tunnel_server() -> Server[TunnelConnectService]:
    """
    Get a server instance for the tunnel connect service.
    """
    tunnel_connect = TunnelConnect()
    server_handler = TunnelConnectService(tunnel_connect)
    return Server(service=server_handler)

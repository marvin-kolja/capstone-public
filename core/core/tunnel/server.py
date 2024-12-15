import asyncio
import inspect
import logging
from abc import ABC
from datetime import timedelta

from types import MethodType
from typing import Optional, TypeVar, Generic

from pydantic import BaseModel
from pymobiledevice3.exceptions import DeviceNotFoundError, NoDeviceConnectedError

from core.codec.socket_json_codec import ServerSocketMessageJSONCodec, SuccessResponse, ErrorResponse, ClientRequest, \
    ServerResponse
from core.exceptions.socket import InvalidSocketMessage
from core.exceptions.tunnel_connect import TunnelAlreadyExistsError
from core.async_socket import ServerSocket
from core.tunnel.interface import TunnelConnectInterface, TunnelResult
from core.tunnel.server_exceptions import MalformedRequestError, TunnelServerError, TunnelServerErrorCode, \
    NotFoundError, InternalServerError, CoreServerError, ServerErrorCode, CriticalServerError
from core.tunnel.tunnel_connect import TunnelConnect

logger = logging.getLogger(__name__)


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
        logger.warning(f"Server method is not a method: {type(func)}")
        raise TypeError
    if not hasattr(func, '__server__'):
        logger.warning(f"Server method does not have __server__ attribute")
        raise AttributeError
    if not hasattr(func, '__signature__'):
        logger.warning(f"Server method does not have __signature__ attribute")
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
            logger.debug(f"Attribute {key} does not exist on {self.__class__.__name__}")
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
            logger.critical("Argument tunnel_connect is None")
            raise ValueError
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
        # TODO: Handle not paired exception.

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
        logger.debug("Cleaning up TunnelConnectService")
        await self.tunnel_connect.close()


SERVICE = TypeVar('SERVICE', bound=ServerMethodHandler)


class Server(Generic[SERVICE]):
    """
    A class to run a socket server that handles requests and responses using a ServerMethodHandler.

    Messages are encoded and decoded using the ServerSocketMessageJSONCodec.
    """

    def __init__(self, service: SERVICE):
        if service is None or not isinstance(service, ServerMethodHandler):
            logger.critical(f"Invalid service provided: {service.__class__.__name__}")
            raise ValueError()
        self._service: SERVICE = service
        self._server_task: Optional[asyncio.Task] = None

    async def __server_task(self, port: int, queue: asyncio.Queue):
        try:
            with ServerSocket(port=port, codec=ServerSocketMessageJSONCodec()) as server:
                logger.info(f"Server started to listen on port {port}")
                queue.put_nowait(True)
                queue = None

                while True:
                    await asyncio.sleep(0)
                    try:
                        await self._process_incoming_request(server)
                    except asyncio.CancelledError:
                        logger.debug("Server task was cancelled while handling request")
                        raise
                    except CriticalServerError as e:
                        logger.critical(
                            f"Stopping server because critical server error occurred while handling request: {e.error}",
                            exc_info=True)
                        break

        finally:
            if queue is not None:
                queue.put_nowait(False)
            self._server_task = None
            await self._service.cleanup()

    async def _process_incoming_request(self, server: ServerSocket):
        """
        Process an incoming request from the client.

        :raises CriticalServerError: If an unexpected error occurs and is unable to send a response.
        :raises asyncio.CancelledError:
        """
        response = None

        try:
            logger.debug("Waiting for request from client")
            request = await self._await_request(server)

            if request is None:
                return

            method = self._get_method(request.action)
            kwargs = self._bind_arguments(method, request.data)
            result = await self._call_method(method, kwargs)
            response = self._construct_response_from_result(result)

        except CoreServerError as e:
            logger.error(f"Error handling request: {e.__class__.__name__}")
            response = ErrorResponse(error_code=e.error_code.value)
        except CriticalServerError:
            raise
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            logger.critical(f"Unexpected error handling request: {e}", exc_info=True)
            response = ErrorResponse(error_code=ServerErrorCode.INTERNAL.value)
        finally:
            if response is not None:
                await self._send_response(server, response)

    @staticmethod
    async def _await_request(server: ServerSocket) -> Optional[ClientRequest]:
        """
        Await a request from the client.

        :return: The request if it was received. If the request times out, None is returned.

        :raises MalformedRequestError: If the socket message is invalid.
        :raises CriticalServerError: If an unexpected error occurs.
        :raises asyncio.CancelledError:
        """
        try:
            return await server.receive(timeout=timedelta(seconds=360))
        except TimeoutError:
            logger.debug("Server request timeout")
            return None
        except InvalidSocketMessage:
            logger.error("Invalid socket message received")
            raise MalformedRequestError()
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            logger.critical(f"Unable to receive a request: {e}", exc_info=True)
            raise CriticalServerError(e)

    @staticmethod
    async def _send_response(server: ServerSocket, response: ServerResponse):
        """
        Send a response to the client.

        If the response fails to send and is not an internal server error response, it will try to send an internal
        server error response. If that also fails, it will raise a CriticalServerError.

        :raises CriticalServerError: If unable to send the response.
        :raises asyncio.CancelledError:
        """
        try:
            await server.respond(response)
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            logger.critical(f"Unable to send response: {e}", exc_info=True)
            if isinstance(response, ErrorResponse):
                if response.error_code == ServerErrorCode.INTERNAL.value:
                    raise CriticalServerError(e)
            logger.info(f"Trying to send internal server error response")
            await Server._send_response(server, ErrorResponse(error_code=ServerErrorCode.INTERNAL.value))

    def _get_method(self, method_name: str) -> MethodType:
        """
        :raises NotFoundError: If the method does not exist.
        """
        try:
            attribute = self._service[method_name]
            return check_server_method(attribute)
        except (KeyError, AttributeError, TypeError) as e:
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
            logger.critical(f"Response data does not follow the expected types: {result.__class__.__name__}")
            raise InternalServerError()

    async def serve(self, port: int):
        """
        Start a server task

        Will wait for the server to start correctly. For this a queue is used to signal if the server has started.

        :raises any Exception: raised by the server task.
        """
        queue = asyncio.Queue()
        task = asyncio.create_task(self.__server_task(port=port, queue=queue))
        self._server_task = task
        logger.debug("Waiting for server to start")
        started = await queue.get()
        if not started:
            logger.warning("Server did not start correctly")
            task.result()

    async def await_close(self):
        """
        Await the server task and raise any exceptions that caused the server task to close.

        If the server task was cancelled, it will not raise an exception.
        """
        try:
            logger.debug("Awaiting server task to close")
            task = self._server_task
            await task
            logger.debug("Server task closed")
            task.result()
            logger.debug("Server task closed without errors")
        except asyncio.CancelledError:
            logger.debug("Server task was cancelled")

    def stop(self):
        """
        Cancels the server task if it exists

        NOTE: Please use `await_close` to wait for the server to close.
        """
        task = self._server_task
        if task is None:
            logger.warning("Server task is not running")
            return

        logger.debug("Cancelling server task")
        task.cancel()


def get_tunnel_server() -> Server[TunnelConnectService]:
    """
    Get a server instance for the tunnel connect service.
    """
    tunnel_connect = TunnelConnect()
    server_handler = TunnelConnectService(tunnel_connect)
    return Server(service=server_handler)

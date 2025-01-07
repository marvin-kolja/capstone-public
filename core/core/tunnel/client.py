import logging
from contextlib import contextmanager
from datetime import timedelta
from typing import Optional

from pymobiledevice3.exceptions import DeviceNotFoundError, NoDeviceConnectedError

from core.codec.socket_json_codec import (
    ClientSocketMessageJSONCodec,
    ClientRequest,
    ErrorResponse,
)
from core.exceptions.tunnel_connect import TunnelAlreadyExistsError
from core.async_socket import ClientSocket
from core.tunnel.server_exceptions import (
    ServerErrorCode,
    InternalServerError,
    MalformedRequestError,
    NotFoundError,
    TunnelServerErrorCode,
)
from core.tunnel.interface import TunnelConnectInterface, TunnelResult

logger = logging.getLogger(__name__)


def get_error_from_context(
    request: ClientRequest, error_response: ErrorResponse
) -> Exception:
    """
    Parses the error response and returns the appropriate error. The request is used to get the data that caused the
    error.

    :param request: The request that caused the error.
    :param error_response: The error response from the server.
    :return Exception: The appropriate exception for the error response.

    :raises ValueError: If the error code in the response is unknown.
    """
    error_code = error_response.error_code

    if error_code == ServerErrorCode.INTERNAL:
        return InternalServerError()
    elif error_code == ServerErrorCode.MALFORMED_REQUEST:
        return MalformedRequestError()
    elif error_code == ServerErrorCode.NOT_FOUND:
        return NotFoundError()
    elif error_code == TunnelServerErrorCode.DEVICE_NOT_FOUND:
        udid = request.data.get("udid")
        return DeviceNotFoundError(udid=udid)
    elif error_code == TunnelServerErrorCode.NO_DEVICE_CONNECTED:
        return NoDeviceConnectedError()
    elif error_code == TunnelServerErrorCode.TUNNEL_ALREADY_EXISTS:
        return TunnelAlreadyExistsError()
    else:
        raise ValueError(f"Unknown error code: {error_code}")


class Client:
    """
    A client class to communicate with the `Server`.

    The client is expected to be used as a context manager.

    The class uses a `ClientSocket` to communicate with the server.
    """

    def __init__(self, port: int, timeout: timedelta):
        """
        Initialize the client with the given port.

        This does not connect to the server. The connection is established when the client is used as a context manager.

        :param port: The port to connect to.
        :param timeout: The timeout for receiving responses.
        """
        self._socket: Optional[ClientSocket] = None
        self._port = port
        self._timeout = timeout

    def __enter__(self):
        logger.debug(f"Entering {self.__class__.__name__} context manager")
        self._socket = ClientSocket(
            port=self._port, codec=ClientSocketMessageJSONCodec()
        ).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"Exiting {self.__class__.__name__} context manager")
        self._socket.__exit__(exc_type, exc_val, exc_tb)

    async def _call_server(self, action: str, **kwargs) -> dict:
        """
        Call the server with the given action and data.

        :param action: The action/method to call on the server.
        :param kwargs: any data to send to the server.

        :return: The response data.

        :raises InvalidSocketMessage: If the request or response are invalid.
        :raises Exception: Parsed server errors, see `get_error_from_context`.
        """
        request = ClientRequest(action=action, data=kwargs)
        logger.debug(f"Calling server with action: {action}")
        await self._socket.send(request)
        response = await self._socket.receive(timeout=self._timeout)

        if isinstance(response, ErrorResponse):
            logger.error(
                f"Received error response from server",
                extra={"response": response.model_dump()},
            )
            raise get_error_from_context(request, response)
        logger.debug(
            f"Received response from server", extra={"response": response.model_dump()}
        )
        return response.data


class TunnelClient(Client, TunnelConnectInterface):
    """
    Implementation of the TunnelConnectInterface for the client side.

    Inherits the `Client` for communication with the server.
    """

    async def start_tunnel(self, udid: str) -> TunnelResult:
        """
        Implementation of the :func:`core.tunnel.interface.TunnelConnectInterface.start_tunnel` method.

        :raises CoreServerError: If the server returns an error that is not a tunnel error.
        :raises TunnelAlreadyExistsError: If a tunnel to the device already exists.
        :raises DeviceNotFoundError: If the device with the UDID is not found.
        :raises NoDeviceConnectedError: If no device is connected.
        """
        data = await self._call_server("start_tunnel", udid=udid)
        return TunnelResult(**data)

    async def stop_tunnel(self, udid: str) -> None:
        await self._call_server("stop_tunnel", udid=udid)

    async def get_tunnel(self, udid: str) -> Optional[TunnelResult]:
        try:
            data = await self._call_server("get_tunnel", udid=udid)
        except NotFoundError:
            return None
        return TunnelResult(**data)


@contextmanager
def get_tunnel_client(port: int, timeout: Optional[timedelta] = None) -> TunnelClient:
    """
    Get a tunnel client instance.

    :param port: The port to connect to.
    :param timeout: The timeout for receiving responses.
    """
    with TunnelClient(port=port, timeout=timeout) as client:
        yield client

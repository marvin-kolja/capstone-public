import logging
from datetime import timedelta
from typing import Optional, Generic

import zmq.asyncio

from core.codec.codec_protocol import E_INPUT, D_OUTPUT, CodecProtocol
from core.codec.socket_json_codec import ClientSocketMessageJSONCodec, ServerSocketMessageJSONCodec
from core.exceptions.socket import InvalidSocketMessage

logger = logging.getLogger(__name__)


class Socket(Generic[E_INPUT, D_OUTPUT]):
    _address = '127.0.0.1'
    _protocol = 'tcp'

    def __init__(self, codec: CodecProtocol[E_INPUT, D_OUTPUT]):
        if not isinstance(codec, CodecProtocol):
            logger.error(f"Invalid codec provided: {codec.__class__.__name__}")
            raise ValueError("Invalid codec")
        self._zmq_context = zmq.asyncio.Context()
        self._socket: Optional[zmq.asyncio.Socket] = None
        self._codec = codec

    def __enter__(self):
        return self

    def __exit__(self, *args):
        logger.debug("Exiting socket context")
        self.close()

    async def receive(self) -> D_OUTPUT:
        message = await self._socket.recv_multipart()
        logger.debug(f"Received multipart message with {len(message)} parts")
        if len(message) != 1:
            logger.error(f"Received message does not have exactly one part ({len(message)} parts)")
            raise InvalidSocketMessage()
        return self._codec.decode_message(message[0])

    def close(self):
        if self._socket is not None:
            logger.debug(f"Closing ZMQ socket of {self.__class__.__name__}")
            self._socket.close()
            self._socket = None
        logger.debug(f"Terminating ZMQ context of {self.__class__.__name__}")
        self._zmq_context.term()


def _timedelta_to_milliseconds(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1e3)


class ClientSocket(Socket[E_INPUT, D_OUTPUT]):
    def __init__(self, port: int, codec: Optional[CodecProtocol[E_INPUT, D_OUTPUT]] = None):
        """
        :param port:
        :param codec: The codec to use to encode/decode messages (default: ClientSocketMessageJSONCodec)
        """
        if codec is None:
            logger.debug("No codec provided, using default ClientSocketMessageJSONCodec")
            codec = ClientSocketMessageJSONCodec()
        super().__init__(codec=codec)
        self._port = port

    def __enter__(self):
        self.connect()
        return self

    def connect(self):
        self._socket = self._zmq_context.socket(zmq.REQ)
        address = f"{self._protocol}://{self._address}:{self._port}"
        logger.debug(f"Connecting to server at {address}")
        self._socket.connect(address)
        self._socket.setsockopt(zmq.LINGER, 0)

    async def receive(self, timeout: Optional[timedelta] = None) -> D_OUTPUT:
        if timeout is None:
            timeout = timedelta(seconds=0.1)

        poller = zmq.asyncio.Poller()
        poller.register(self._socket, zmq.POLLIN)

        timeout_milliseconds = _timedelta_to_milliseconds(timeout)

        logger.debug(f"Polling response with timeout of {timeout_milliseconds}ms")
        socks = dict(await poller.poll(timeout_milliseconds))
        if self._socket in socks and socks[self._socket] == zmq.POLLIN:
            return await super().receive()
        else:
            raise TimeoutError("Server response timeout")

    async def send(self, message: E_INPUT):
        logger.debug(f"Sending request to server")
        await self._socket.send_multipart([self._codec.encode_message(message)])


class ServerSocket(Socket[E_INPUT, D_OUTPUT]):

    def __init__(self, port: Optional[int] = None, codec: Optional[CodecProtocol[E_INPUT, D_OUTPUT]] = None):
        """
        :param port:
        :param codec: The codec to use to encode/decode messages (default: ServerSocketMessageJSONCodec)
        """
        if codec is None:
            logger.debug("No codec provided, using default ServerSocketMessageJSONCodec")
            codec = ServerSocketMessageJSONCodec()
        super().__init__(codec=codec)
        self.__port: Optional[int] = port

    @property
    def port(self) -> int:
        return self.__port

    def __enter__(self):
        self.start()
        return self

    def start(self):
        self._socket = self._zmq_context.socket(zmq.REP)
        address = f"{self._protocol}://{self._address}"
        if self.__port is None:
            logger.debug(f"Binding socket to random port with {address}")
            self.__port = self._socket.bind_to_random_port(address)
        else:
            address_with_port = f"{address}:{self.__port}"
            logger.debug(f"Binding socket to {address_with_port}")
            self._socket.bind(address_with_port)
        logger.debug(f"Bound socket to port {self.__port}")

    async def receive(self, timeout: Optional[timedelta] = None) -> D_OUTPUT:
        if timeout is None:
            timeout = timedelta(seconds=0.1)
        self._socket.setsockopt(zmq.RCVTIMEO, _timedelta_to_milliseconds(timeout))
        try:
            return await super().receive()
        except zmq.error.Again:
            logger.debug("Did not receive message within timeout")
            raise TimeoutError()

    async def respond(self, message: E_INPUT):
        logger.debug("Sending response to client")
        await self._socket.send_multipart([self._codec.encode_message(message)])

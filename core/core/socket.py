from datetime import timedelta
from typing import Optional

import zmq.asyncio

from core.codec.socket_json_codec import SocketMessageJSONCodec, BaseMessage, ClientSocketMessageJSONCodec, \
    ServerSocketMessageJSONCodec, ClientRequest, ServerResponse
from core.exceptions.socket import InvalidSocketMessage


class Socket:
    _address = '127.0.0.1'
    _protocol = 'tcp'

    def __init__(self, codec: SocketMessageJSONCodec = SocketMessageJSONCodec()):
        if not isinstance(codec, SocketMessageJSONCodec):
            raise ValueError("Invalid codec")
        self._zmq_context = zmq.asyncio.Context()
        self._socket: Optional[zmq.asyncio.Socket] = None
        self._codec = codec

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def receive(self) -> BaseMessage:
        message = await self._socket.recv_multipart()
        if len(message) != 1:
            raise InvalidSocketMessage("Only one message is expected")
        return self._codec.decode_message(message[0])

    def close(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        self._zmq_context.term()


def _timedelta_to_milliseconds(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1e3)


class ClientSocket(Socket):
    def __init__(self, port: int, codec: Optional[ClientSocketMessageJSONCodec] = None):
        if codec is None:
            codec = ClientSocketMessageJSONCodec()
        super().__init__(codec=codec)
        self._port = port

    def __enter__(self):
        self.connect()
        return self

    def connect(self):
        self._socket = self._zmq_context.socket(zmq.REQ)
        self._socket.connect(f"{self._protocol}://{self._address}:{self._port}")
        self._socket.setsockopt(zmq.LINGER, 0)

    async def receive(self, timeout: Optional[timedelta] = None) -> ServerResponse:
        if timeout is None:
            timeout = timedelta(seconds=0.1)

        poller = zmq.asyncio.Poller()
        poller.register(self._socket, zmq.POLLIN)

        socks = dict(await poller.poll(_timedelta_to_milliseconds(timeout)))
        if self._socket in socks and socks[self._socket] == zmq.POLLIN:
            return await super().receive()
        else:
            raise TimeoutError("Server response timeout")

    async def send(self, message: ClientRequest):
        await self._socket.send_multipart([self._codec.encode_message(message)])


class ServerSocket(Socket):

    def __init__(self, port: Optional[int] = None, codec: Optional[ServerSocketMessageJSONCodec] = None):
        if codec is None:
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
        if self.__port is None:
            self.__port = self._socket.bind_to_random_port(f"{self._protocol}://{self._address}")
        else:
            self._socket.bind(f"{self._protocol}://{self._address}:{self.__port}")

    async def receive(self, timeout: Optional[timedelta] = None) -> ClientRequest:
        if timeout is None:
            timeout = timedelta(seconds=0.1)
        self._socket.setsockopt(zmq.RCVTIMEO, _timedelta_to_milliseconds(timeout))
        try:
            return await super().receive()
        except zmq.error.Again:
            raise TimeoutError()

    async def respond(self, message: ServerResponse):
        await self._socket.send_multipart([self._codec.encode_message(message)])

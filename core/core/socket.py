import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

import zmq.asyncio
from pydantic import BaseModel, field_validator, Field, ValidationError

from core.exceptions.socket import InvalidSocketMessage


class BaseMessage(BaseModel):
    message_type: str
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1e3))

    @field_validator("timestamp")
    def validate_unix_timestamp(cls, value: int) -> int:
        try:
            # Check if it's a valid Unix timestamp
            cls.__timestamp_to_datetime(value)
            return value
        except (ValueError, OSError):
            raise ValueError("Invalid Unix timestamp")

    @staticmethod
    def __timestamp_to_datetime(timestamp: int) -> datetime:
        return datetime.fromtimestamp(timestamp / 1e3, tz=timezone.utc)

    @property
    def timestamp_as_datetime(self) -> datetime:
        return self.__timestamp_to_datetime(self.timestamp)

    def encode(self) -> bytes:
        """
        Encode message data to bytes for sending over socket
        """
        return self.model_dump_json().encode()


class ClientRequest(BaseMessage):
    message_type: str = "request"
    action: str
    data: Optional[dict] = None


class HeartbeatRequest(ClientRequest):
    action: str = "heartbeat"


class ServerResponse(BaseMessage):
    message_type: str = "response"
    status: str
    message: Optional[str] = None


class ErrorResponse(ServerResponse):
    status: str = "ERROR"
    error_code: int


class SuccessResponse(ServerResponse):
    status: str = "OK"
    data: Optional[dict] = None


class SocketMessageFactory:

    @staticmethod
    def parse_message_data(message_data: dict) -> Union[ClientRequest, ServerResponse]:
        """
        Parse message data and return corresponding message class instance based on `message_type` field
        and message type specific fields.

        :exception InvalidSocketMessage: If unable to identify corresponding class from message data or a validation
        error occurs.
        """
        try:
            if message_data.get("timestamp") is None:
                raise InvalidSocketMessage("Timestamp is required")
            message_type = message_data.get("message_type")
            if message_type is None:
                raise InvalidSocketMessage("Message type is required")

            if message_type == "response":
                status = message_data.get("status")
                if status == "ERROR":
                    return ErrorResponse(**message_data)
                elif status == "OK":
                    return SuccessResponse(**message_data)
                else:
                    raise InvalidSocketMessage(f"Unknown server response status: {status}")
            elif message_type == "request":
                action = message_data.get("action")
                if action == "heartbeat":
                    return HeartbeatRequest(**message_data)
                return ClientRequest(**message_data)
            else:
                raise InvalidSocketMessage(f"Unknown message type: {message_type}")
        except ValidationError as e:
            raise InvalidSocketMessage(str(e))


class SocketMessageCodec:
    @staticmethod
    def encode_message(message: BaseMessage) -> bytes:
        """
        Encode message data to bytes for sending over socket
        """
        return message.encode()

    @staticmethod
    def decode_message(message: bytes) -> BaseMessage:
        """
        Decode message data from bytes received over socket
        """
        try:
            decoded_message = json.loads(message.decode())
        except json.JSONDecodeError:
            raise InvalidSocketMessage("Invalid JSON data")
        except UnicodeDecodeError:
            raise InvalidSocketMessage("Invalid UTF-8 data")

        if not isinstance(decoded_message, dict):
            raise InvalidSocketMessage("Data must be a JSON object")

        return SocketMessageFactory.parse_message_data(decoded_message)


class ClientSocketMessageCodec(SocketMessageCodec):
    @staticmethod
    def encode_message(message: BaseMessage) -> bytes:
        if not isinstance(message, ClientRequest):
            raise InvalidSocketMessage("Invalid client request")
        return SocketMessageCodec.encode_message(message)

    @staticmethod
    def decode_message(message: bytes) -> ServerResponse:
        decoded_message = SocketMessageCodec.decode_message(message)
        if not isinstance(decoded_message, ServerResponse):
            raise InvalidSocketMessage("Invalid server response")
        return decoded_message


class ServerSocketMessageCodec(SocketMessageCodec):
    @staticmethod
    def encode_message(message: BaseMessage) -> bytes:
        if not isinstance(message, ServerResponse):
            raise InvalidSocketMessage("Invalid server response")
        return SocketMessageCodec.encode_message(message)

    @staticmethod
    def decode_message(message: bytes) -> ClientRequest:
        decoded_message = SocketMessageCodec.decode_message(message)
        if not isinstance(decoded_message, ClientRequest):
            raise InvalidSocketMessage("Invalid client request")
        return decoded_message


class Socket:
    _address = '127.0.0.1'

    def __init__(self, codec: SocketMessageCodec = SocketMessageCodec()):
        if not isinstance(codec, SocketMessageCodec):
            raise ValueError("Invalid codec")
        self._zmq_context = zmq.asyncio.Context()
        self._socket: Optional[zmq.asyncio.Socket] = None
        self._codec = codec

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        self._zmq_context.term()


class ClientSocket(Socket):
    def __init__(self, port: int, codec: Optional[ClientSocketMessageCodec] = None):
        if codec is None:
            codec = ClientSocketMessageCodec()
        super().__init__(codec=codec)
        self._port = port

    def __enter__(self):
        self.connect()
        return self

    def connect(self):
        self._socket = self._zmq_context.socket(zmq.REQ)
        self._socket.connect(f"tcp://{self._address}:{self._port}")
        self._socket.setsockopt(zmq.LINGER, 0)

    async def receive(self, timeout: Optional[timedelta] = None) -> ServerResponse:
        if timeout is None:
            timeout = timedelta(seconds=0.1)

        poller = zmq.asyncio.Poller()
        poller.register(self._socket, zmq.POLLIN)

        socks = dict(await poller.poll(timeout.microseconds // 1000))
        if self._socket in socks and socks[self._socket] == zmq.POLLIN:
            response = await self._socket.recv_multipart()
            return self._codec.decode_message(response[0])
        else:
            raise TimeoutError("Server response timeout")

    async def send(self, message: ClientRequest):
        await self._socket.send_multipart([self._codec.encode_message(message)])


class ServerSocket(Socket):

    def __init__(self, port: Optional[int] = None, codec: Optional[ServerSocketMessageCodec] = None):
        if codec is None:
            codec = ServerSocketMessageCodec()
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
            self.__port = self._socket.bind_to_random_port(f"tcp://{self._address}")
        else:
            self._socket.bind(f"tcp://{self._address}:{self.__port}")

    async def receive(self, timeout: timedelta = timedelta(seconds=0.1)) -> ClientRequest:
        raise NotImplementedError()

    async def respond(self, message: ServerResponse):
        raise NotImplementedError()

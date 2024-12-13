import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Union, Generic

from pydantic import field_validator, BaseModel, Field, ValidationError

from core.codec.codec_protocol import CodecProtocol, E_INPUT, D_OUTPUT
from core.codec.json_codec import JSONCodec
from core.exceptions.socket import InvalidSocketMessage

logger = logging.getLogger(__name__)


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
                logger.error("Timestamp is required when parsing message data")
                raise InvalidSocketMessage
            message_type = message_data.get("message_type")
            if message_type is None:
                logger.error("Message type is required when parsing message data")
                raise InvalidSocketMessage

            if message_type == "response":
                status = message_data.get("status")
                if status == "ERROR":
                    return ErrorResponse(**message_data)
                elif status == "OK":
                    return SuccessResponse(**message_data)
                else:
                    logger.error(f"Unknown server response status: {status}")
                    raise InvalidSocketMessage
            elif message_type == "request":
                action = message_data.get("action")
                if action == "heartbeat":
                    return HeartbeatRequest(**message_data)
                return ClientRequest(**message_data)
            else:
                logger.error(f"Unknown message type: {message_type}")
                raise InvalidSocketMessage
        except ValidationError as e:
            logger.error(f"Failed to validate message data: {e}", exc_info=True)
            raise InvalidSocketMessage


class SocketMessageJSONCodec(CodecProtocol[BaseMessage, BaseMessage], Generic[E_INPUT, D_OUTPUT]):
    @staticmethod
    def encode_message(message: BaseMessage) -> bytes:
        """
        Encode message data to bytes for sending over socket
        """
        return JSONCodec.encode_message(message)

    @staticmethod
    def decode_message(message: bytes) -> BaseMessage:
        """
        Decode message data from bytes received over socket
        """
        try:
            decoded_message = JSONCodec.decode_message(message)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {e}", exc_info=True)
            raise InvalidSocketMessage()
        except UnicodeDecodeError as e:
            logger.error(f"Invalid UTF-8 data: {e}", exc_info=True)
            raise InvalidSocketMessage()

        if not isinstance(decoded_message, dict):
            logger.error("Data must be a JSON object")
            raise InvalidSocketMessage()

        return SocketMessageFactory.parse_message_data(decoded_message)


def check_client_request(message: BaseMessage) -> ClientRequest:
    if not isinstance(message, ClientRequest):
        logger.error(f"Message is not a client request: {type(message)}")
        raise InvalidSocketMessage()
    return message


def check_server_response(message: BaseMessage) -> ServerResponse:
    if not isinstance(message, ServerResponse):
        logger.error(f"Message is not a server response: {type(message)}")
        raise InvalidSocketMessage()
    return message


class ClientSocketMessageJSONCodec(SocketMessageJSONCodec[ClientRequest, ServerResponse]):
    @staticmethod
    def encode_message(message: BaseMessage) -> bytes:
        return SocketMessageJSONCodec.encode_message(check_client_request(message))

    @staticmethod
    def decode_message(message: bytes) -> ServerResponse:
        decoded_message = SocketMessageJSONCodec.decode_message(message)
        return check_server_response(decoded_message)


class ServerSocketMessageJSONCodec(SocketMessageJSONCodec[ServerResponse, ClientRequest]):
    @staticmethod
    def encode_message(message: BaseMessage) -> bytes:
        return SocketMessageJSONCodec.encode_message(check_server_response(message))

    @staticmethod
    def decode_message(message: bytes) -> ClientRequest:
        decoded_message = SocketMessageJSONCodec.decode_message(message)
        return check_client_request(decoded_message)

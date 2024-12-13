import json
import logging
from typing import Any

from pydantic import BaseModel

from core.codec.codec_protocol import CodecProtocol

logger = logging.getLogger(__name__)


class JSONCodec(CodecProtocol[Any, Any]):
    @staticmethod
    def encode_message(message: Any) -> bytes:
        """
        Encode message to bytes using `json.dumps` or `model_dump_json` for Pydantic models
        """
        if isinstance(message, BaseModel):
            logger.debug(f"Encoding message of type {message.__class__.__name__}")
            return message.model_dump_json().encode()
        logger.debug(f"Encoding message of type {type(message).__name__}")
        return json.dumps(message).encode()

    @staticmethod
    def decode_message(message: bytes) -> Any:
        """
        Decode message from bytes using `json.loads`
        """
        logger.debug(f"Decoding message bytes")
        loaded_json = json.loads(message.decode())
        logger.debug(f"Decoded message to type {type(loaded_json).__name__}")
        return loaded_json

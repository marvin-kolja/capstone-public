import json
from typing import Any

from pydantic import BaseModel

from core.codec.codec_protocol import CodecProtocol


class JSONCodec(CodecProtocol[Any, Any]):
    @staticmethod
    def encode_message(message: Any) -> bytes:
        """
        Encode message to bytes using `json.dumps` or `model_dump_json` for Pydantic models
        """
        if isinstance(message, BaseModel):
            return message.model_dump_json().encode()
        return json.dumps(message).encode()

    @staticmethod
    def decode_message(message: bytes) -> Any:
        """
        Decode message from bytes using `json.loads`
        """
        return json.loads(message.decode())

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

E_INPUT = TypeVar('E_INPUT')
D_OUTPUT = TypeVar('D_OUTPUT')


class CodecProtocol(ABC, Generic[E_INPUT, D_OUTPUT]):
    """
    Abstract class for encoding and decoding messages to and from bytes
    """

    @staticmethod
    @abstractmethod
    def encode_message(message: E_INPUT) -> bytes:
        """
        Encode message data into bytes
        """

    @staticmethod
    @abstractmethod
    def decode_message(message: bytes) -> D_OUTPUT:
        """
        Decode bytes into message data
        """

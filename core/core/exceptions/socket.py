__all__ = [
    "InvalidSocketMessage",
]

from core.exceptions import CoreException


class SocketError(CoreException):
    """Socket related error"""

    pass


class InvalidSocketMessage(SocketError):
    """Invalid socket message"""

    def __init__(self):
        super().__init__()

__all__ = [
    'InvalidSocketMessage',
]

from core.exceptions import CoreException


class SocketError(CoreException):
    """ Socket related error"""
    pass


class InvalidSocketMessage(SocketError):
    """ Invalid socket message"""

    def __init__(self, message_data):
        self.message_data = message_data
        super().__init__()

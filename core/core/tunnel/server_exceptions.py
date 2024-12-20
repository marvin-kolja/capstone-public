from enum import IntEnum


class ServerErrorCode(IntEnum):
    INTERNAL = 0
    MALFORMED_REQUEST = 1
    NOT_FOUND = 2


class CoreServerError(Exception):
    def __init__(self, error_code: IntEnum):
        super().__init__()
        self.error_code = error_code


class InternalServerError(CoreServerError):
    def __init__(self):
        super().__init__(error_code=ServerErrorCode.INTERNAL)


class MalformedRequestError(CoreServerError):
    def __init__(self):
        super().__init__(error_code=ServerErrorCode.MALFORMED_REQUEST)


class NotFoundError(CoreServerError):
    def __init__(self):
        super().__init__(error_code=ServerErrorCode.NOT_FOUND)


class TunnelServerErrorCode(IntEnum):
    DEVICE_NOT_FOUND = 100
    NO_DEVICE_CONNECTED = 101
    TUNNEL_ALREADY_EXISTS = 102


class TunnelServerError(CoreServerError):
    def __init__(self, error_code: TunnelServerErrorCode):
        super().__init__(error_code=error_code)


class CriticalServerError(Exception):
    """A critical server error that the server cannot handle"""

    def __init__(self, error: BaseException):
        self.error = error

from core.exceptions import CoreException

__all__ = [
    "TunnelAlreadyExistsError",
]


class TunnelConnectError(CoreException):
    """Tunnel connect error"""

    pass


class TunnelAlreadyExistsError(TunnelConnectError):
    """A tunnel to the device already exists"""

    pass

from core.exceptions import CoreException

__all__ = [
    "InvalidFileContent",
]

class InvalidFileContent(CoreException):
    """
    Raised when the content of the file is invalid.
    """
    pass

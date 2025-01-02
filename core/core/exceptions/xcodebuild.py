from core.exceptions import CoreException

__all__ = [
    "XcodebuildException",
]

class XcodebuildException(CoreException):
    """
    Raised when the xcodebuild command process fails.
    """

    stderr: list[str]
    stdout: list[str]
    return_code: int

    def __init__(self, stderr, stdout, return_code):
        """
        :param stderr:
        :param stdout:
        :param return_code: The return code of the xcodebuild command process
        """
        self.stderr = stderr
        self.stdout = stdout
        self.return_code = return_code



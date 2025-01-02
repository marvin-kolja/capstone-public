from core.exceptions import CoreException

__all__ = [
    "ListEnumerationFailure",
]


class ListEnumerationFailure(CoreException):
    """
    Raised when the result of the test enumeration contains errors.
    """

    stderr: list[str]
    stdout: list[str]
    errors: list[str]

    def __init__(self, stderr, stdout, errors):
        """
        :param stderr:
        :param stdout:
        :param errors: List of errors extracted from the test enumeration result.
        """
        self.stderr = stderr
        self.stdout = stdout
        self.errors = errors

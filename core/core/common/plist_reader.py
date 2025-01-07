import plistlib
from typing import Any

from core.exceptions.common import InvalidFileContent


def read_plist(path: str) -> dict[str, Any]:
    """
    Read the content of the plist file and return it as a dictionary.

    Does not check if the file exists and simply tries to read the file.

    :param path: The path to the plist file.
    :return: The content of the plist file as a dictionary.
    :raises: `InvalidFileContent` when parsing the plist file fails.
    :raises: `FileNotFoundError` when the file does not exist.
    """
    with open(path, "rb") as file:
        try:
            result = plistlib.load(file)
        except Exception as e:
            raise InvalidFileContent(f"Failed to parse plist file '{path}'") from e
        if not isinstance(result, dict):
            raise InvalidFileContent(
                f"Plist file '{path}' content is not a dictionary."
            )
        return result

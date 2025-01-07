import logging

from core.app.info_plist import InfoPlist

logger = logging.getLogger(__name__)


class XcApp:
    """
    Allows to interact with a .app package.
    """

    def __init__(self, path: str):
        """
        :param path: The path to the .app package.
        """
        logger.debug(f"Initializing XcApp with path: {path}")
        self._path = path

    def parse_info_plist(self) -> InfoPlist:
        """
        Reads the Info.plist file from the .app package and parses it.

        :return: The parsed Info.plist file

        :raises: `FileNotFoundError` when the Info.plist file is not found.
        """
        raise NotImplementedError

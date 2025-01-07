import logging
import pathlib

from core.app.info_plist import InfoPlist
from core.common.plist_reader import read_plist

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

    @property
    def path(self) -> str:
        """
        The path to the .app package.
        """
        return self._path

    def parse_info_plist(self) -> InfoPlist:
        """
        Reads the Info.plist file from the .app package and parses it.

        :return: The parsed Info.plist file

        :raises FileNotFoundError: when the Info.plist file is not found.
        :raises InvalidFileContent:
        """
        info_plist_path = pathlib.Path(self._path, "Info.plist").absolute().as_posix()

        try:
            data = read_plist(info_plist_path)
        except FileNotFoundError:
            logger.warning(f"Info.plist file not found at path: {info_plist_path}")
            raise

        logger.debug(f"Successfully read Info.plist file from path: {info_plist_path}")

        return InfoPlist.model_validate(data)

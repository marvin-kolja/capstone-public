import logging
from typing import Optional

from core.subprocesses.process import ProcessCommand

logger = logging.getLogger(__name__)


class TunnelServerCommand(ProcessCommand):
    def __init__(self, port: int, log_level: Optional[str] = None):
        self.__port = port
        self.__log_level = log_level

    def parse(self) -> [str]:
        command = ["python", "-m", "core.subprocesses.tunnel_server_executable", str(self.__port)]
        if self.__log_level:
            return command + ["--log-level", self.__log_level]
        return command

from enum import StrEnum
from pathlib import Path
from xml.etree import ElementTree
from typing import Optional, Any

from pydantic import BaseModel

from core.xc.xctrace.toc import TOC, ProcessEntry


class Schema(StrEnum):
    SYSMON_PROCESS = "sysmon-process"
    CORE_ANIMATION_FPS_ESTIMATE = "core-animation-fps-estimate"
    STDOUTERR_OUTPUT = "stdouterr-output"

    @staticmethod
    def all():
        return list(map(lambda m: m.value, Schema))


class Sysmon(BaseModel):
    timestamp: int
    cpu: Optional[float]
    memory: Optional[float]
    resident_size: Optional[float]
    recently_died: bool


class CoreAnimation(BaseModel):
    timestamp: int
    fps: float
    gpu_utilization: float


class ProcessStdoutErr(BaseModel):
    timestamp: int
    console_text: str


class XctraceXMLParser:
    """
    Parses data from an XML file containing data that was exported from a trace file using xctrace.

    To parse TOC data, please take a look at :mod:`core.xc.xctrace.toc`.
    """

    def __init__(self, path: Path, toc: TOC) -> None:
        self.__tree = ElementTree.parse(path.absolute().as_posix())
        self.__toc = toc
        self.__cache_map: dict[str, ElementTree.Element] = {}
        self.__root = self.__tree.getroot()

    def parse_sysmon_for_target(
        self,
        run: int,
        target_process: Optional[ProcessEntry] = None,
    ) -> list[Sysmon]:
        """
        Extracts the sysmon data for the target process from the given run.

        :param run: The run number to extract the sysmon data from. The first run is 1.
        :param target_process: The target process to extract the sysmon data for. If None, it will use the target
        process from the TOC, if available.
        :return:
        """
        raise NotImplementedError

    def parse_core_animation(self, run: int) -> list[CoreAnimation]:
        """
        Extracts the core animation data from the given run.
        :param run: The run number to extract the core animation data from. The first run is 1.
        :return: A list of CoreAnimation objects containing the extracted data.
        """
        raise NotImplementedError

    def parse_stdout_err(self, run: int) -> list[ProcessStdoutErr]:
        """
        Extracts the stdout and stderr data from the given run.
        :param run: The run number to extract the stdout and stderr data from. The first run is 1.
        :return: A list of ProcessStdoutErr objects containing the extracted data.
        """
        raise NotImplementedError

    def parse_multiple(self, run: int) -> dict[Schema, Any]:
        """
        Extracts all data from the given run.
        :param run: The run number to extract the data from. The first run is 1.
        :return: A dictionary containing the extracted data for each schema.
        """
        raise NotImplementedError

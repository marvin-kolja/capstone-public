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

    **About Cache Map:**
    Xctrace exports data in a tree structure where elements can reference other elements using a `ref` attribute,
    while the `id` attribute uniquely identifies the referenced element. This mechanism helps reduce redundancy
    in the data. For example, a CPU usage percentage element may have a usage value of `0%`. If another element
    has the same value, instead of duplicating the value, it references the first element using its `ref`.

    To avoid repeatedly traversing the tree to resolve these references, we cache all elements with an `id`
    attribute in a dictionary. This allows for `O(1)` access to elements using their `id`.

    Complexity Analysis:
        - Cache Access: `O(1)`, as lookups in the dictionary are constant-time operations.
        - Cache Construction: `O(m)`, where `m` is the number of elements with an `id` attribute. Typically,
          `m << n`, where `n` is the total number of elements in the tree.
        - Space Complexity: `O(m)`, as the cache stores references to `m` elements with `id` attributes.

    Attributes:
        __tree: The ElementTree object containing the parsed XML data.
        __toc: The TOC object containing the passed TOC data.
        __cache_map: A dictionary mapping the schema to the corresponding XML element.
        __root: The root element of the XML tree.
    """

    def __init__(self, path: Path, toc: TOC) -> None:
        self.__tree = ElementTree.parse(path.absolute().as_posix())
        self.__root = self.__tree.getroot()
        self.__toc = toc
        self.__cache_map: dict[str, ElementTree.Element] = {}

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

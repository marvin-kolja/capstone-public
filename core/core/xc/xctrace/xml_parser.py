import logging
from enum import StrEnum
from pathlib import Path
from xml.etree import ElementTree
from typing import Optional, Any

from pydantic import BaseModel

from core.xc.xctrace.toc import TOC, ProcessEntry

logger = logging.getLogger(__name__)


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
        self._cache_refs(self.__relevant_tag_xpaths)

    def parse_sysmon_for_target(
        self,
        run: int,
        target_process: ProcessEntry,
    ) -> list[Sysmon]:
        """
        Extracts the sysmon data for the target process from the given run.

        :param run: The run number to extract the sysmon data from. The first run is 1.
        :param target_process: The target process to extract the sysmon data for.
        :return:
        """
        table_number = self._get_table_number_for_schema(run, Schema.SYSMON_PROCESS)
        xpath = table_number_xpath(run=run, table_number=table_number)
        rows = self._get_rows(self.__root, node_xpath_attrib=xpath)
        return self._extract_sysmon(rows, target_process)

    def parse_core_animation(self, run: int) -> list[CoreAnimation]:
        """
        Extracts the core animation data from the given run.
        :param run: The run number to extract the core animation data from. The first run is 1.
        :return: A list of CoreAnimation objects containing the extracted data.
        """
        table_number = self._get_table_number_for_schema(
            run, Schema.CORE_ANIMATION_FPS_ESTIMATE
        )
        xpath = table_number_xpath(run=run, table_number=table_number)
        rows = self._get_rows(self.__root, node_xpath_attrib=xpath)
        return self._extract_core_animation(rows)

    def parse_stdout_err(self, run: int) -> list[ProcessStdoutErr]:
        """
        Extracts the stdout and stderr data from the given run.
        :param run: The run number to extract the stdout and stderr data from. The first run is 1.
        :return: A list of ProcessStdoutErr objects containing the extracted data.
        """
        table_number = self._get_table_number_for_schema(run, Schema.STDOUTERR_OUTPUT)
        xpath = table_number_xpath(run=run, table_number=table_number)
        rows = self._get_rows(self.__root, node_xpath_attrib=xpath)
        return self._extract_stdout_err(rows)

    def parse_multiple(
        self,
        run: int,
        target_process: Optional[ProcessEntry] = None,
    ) -> dict[Schema, Any]:
        """
        Extracts all data from the given run.
        :param run: The run number to extract the data from. The first run is 1.
        :param target_process: The target process to extract the sysmon data for. Required if sysmon data is present in
        the toc.
        :return: A dictionary containing the extracted data for each schema.
        :raises ValueError: If the target process is not provided when extracting sysmon data.
        """
        data = {
            Schema.SYSMON_PROCESS: None,
            Schema.STDOUTERR_OUTPUT: None,
            Schema.CORE_ANIMATION_FPS_ESTIMATE: None,
        }

        toc_run = self.__toc.runs[run - 1]
        tables = toc_run.data

        schema_names_in_toc = [table.schema_name for table in tables]

        if Schema.SYSMON_PROCESS in schema_names_in_toc:
            if target_process is None:
                raise ValueError(
                    "Target process must be provided to extract sysmon data."
                )
            data[Schema.SYSMON_PROCESS] = self.parse_sysmon_for_target(
                run, target_process
            )
        if Schema.STDOUTERR_OUTPUT in schema_names_in_toc:
            data[Schema.STDOUTERR_OUTPUT] = self.parse_stdout_err(run)
        if Schema.CORE_ANIMATION_FPS_ESTIMATE in schema_names_in_toc:
            data[Schema.CORE_ANIMATION_FPS_ESTIMATE] = self.parse_core_animation(run)

        return data

    __relevant_tag_xpaths = []
    """
    Relevant xpaths that will be accessed during parsing and should be cached.
    """

    def _cache_refs(self, xpaths: list[str]):
        """
        Caches all elements with an `id` attribute in the XML tree by searching for elements that match the given
        xpaths. All xpaths will be appended using the `[@id]` selector to only match elements with an `id` attribute.

        :param xpaths: A list of xpaths to search for elements with an `id` attribute.
        """
        logger.debug(f"Caching elements with an `id` attribute using xpaths: {xpaths}")
        for xpath in xpaths:
            self._cache_elements(self.__root, f"{xpath}[@id]")
        logger.debug(f"Cached {len(self.__cache_map)} elements.")

    def _cache_elements(self, element: ElementTree.Element, xpath: str):
        """
        Caches all elements with an `id` attribute in the given element subtree by searching for elements that match
        the given xpath.

        :param element: A xml element to search for elements in.
        :param xpath: The xpath to match elements in the element.
        """
        logger.debug(f"Searching for elements to cache matching xpath: {xpath}")
        elements = element.findall(xpath)
        logger.debug(f"Found {len(elements)} elements.")
        for found_element in elements:
            attrib = found_element.attrib
            if attrib.get("id"):
                self.__cache_map[attrib["id"]] = found_element
            else:
                logger.warning(
                    f"Selected element for caching that does not have an `id` attribute."
                )

    def _get_cached_element(
        self,
        element: ElementTree.Element,
        xpath: str,
    ) -> Optional[ElementTree.Element]:
        """
        Retrieve the element that matches the xpath from the cache. Uses the first element if multiple elements are
        found and returns None if no elements are found.

        :param element: The element to search for the element in
        :param xpath: The xpath to match the element
        :return: The matched element
        :raises KeyError: If the element is not found in the cache. If this happens, the cache is not properly built.
        """
        elements = element.findall(xpath)
        if len(elements) == 0:
            return None
        element = elements[0]
        attrib = element.attrib
        if attrib.get("id"):
            logger.debug(
                "No need to get element from cache as it has an `id` attribute."
            )
            return element
        else:
            ref = attrib.get("ref")
            logger.debug(f"Trying to get element from cache using ref '{ref}'")
            return self.__cache_map[ref]

    def _get_table_number_for_schema(self, run: int, schema: Schema) -> int:
        """
        Get the table number for the given schema by looking it up in the TOC.

        :param run: The run number to get the table number for. The first run is 1.
        :param schema: The schema to get the table number for.
        :return: The table number for the given schema. The first table is 1.
        :raises IndexError: If the run number is out of bounds.
        :raises ValueError: If no table number is found for the schema.
        """
        single_run = self.__toc.runs[run - 1]
        for index, data_table in enumerate(single_run.data):
            if data_table.schema_name == schema.value:
                return index + 1

        raise ValueError(f"No table number found for schema {schema}")

    def _extract_sysmon(
        self,
        rows: list[ElementTree.Element],
        target_process: ProcessEntry,
    ) -> list[Sysmon]:
        """
        Extracts the sysmon data from the given rows, matching the target app name or PID.

        :param rows: The rows to extract the sysmon data from.
        :param target_process: The target process to extract the sysmon data for.
        :return: A list of Sysmon objects containing the extracted data.
        """
        raise NotImplementedError

    def _extract_core_animation(
        self, rows: list[ElementTree.Element]
    ) -> list[CoreAnimation]:
        """
        Extracts the core animation data from the given rows.
        :param rows: The rows to extract the core animation data from.
        :return: A list of CoreAnimation objects containing the extracted data.
        """
        raise NotImplementedError

    def _extract_stdout_err(
        self, rows: list[ElementTree.Element]
    ) -> list[ProcessStdoutErr]:
        """
        Extracts the stdout and stderr data from the given rows.
        :param rows: The rows to extract the stdout and stderr data from.
        :return: A list of ProcessStdoutErr objects containing the extracted data.
        """
        raise NotImplementedError

    @staticmethod
    def _get_rows(
        root: ElementTree.Element,
        node_xpath_attrib: Optional[str] = None,
        row_selector: Optional[str] = None,
    ) -> list[ElementTree.Element]:
        """
        Get all rows from nodes where the xpath attribute matches the given xpath.

        :param root: The root element to search for the nodes in.
        :param node_xpath_attrib: The xpath to match the nodes with, if None all nodes will be matched.
        :param row_selector: The selector to match the rows with (e.g. "1" to get the first row). Will be parsed to
        "[<row_selector>]"_.
        :return: A list of all rows from the matched nodes.
        """
        row_selector_parsed = f"[{row_selector}]" if row_selector is not None else ""
        node_selector_parsed = (
            f'[@xpath="{node_xpath_attrib}"]' if node_xpath_attrib is not None else ""
        )
        return root.findall(f".//node{node_selector_parsed}/row{row_selector_parsed}")


def table_xpath(run: int, table_selector: str) -> str:
    """
    When exporting data from the trace file the data is stored in nodes. In order to retrieve the correct node we
    need to provide the correct xpath. This method returns the xpath for a specific run and table number.

    The xpath is in the following format: ``//trace-toc[1]/run[1]/data[1]/table[<table_selector>]``.
    Where the numbers for trace-toc, and data seem to be constant. The run number defines the run to be parsed and
    the table selector which data to extract. The exported data uses a number to identify the table. When exporting
    one can use the schema name to identify the table.

    :param run: The number of the run in the trace file. The first run is 1.
    :param table_selector: The selector to identify the table to extract data from.

    :return: The xpath for the data node
    """
    return f"//trace-toc[1]/run[{run}]/data[1]/table[{table_selector}]"


def table_number_xpath(run: int, table_number: int) -> str:
    """
    Convenience method for the `table_xpath` method to select a specific table number.

    :param run:
    :param table_number: The table number to select the data for.
    """
    return table_xpath(run=run, table_selector=str(table_number))


def table_schemas_xpath(run: int, schemas: list[Schema]) -> str:
    """
    Convenience method for the `table_xpath` method to select multiple schemas.

    :param run:
    :param schemas: The schema names to select the data for.
    """

    if len(schemas) == 0:
        raise ValueError("At least one schema name must be provided")

    table_selector = f"{' or '.join([f'@schema="{schema}"' for schema in schemas])}"

    return table_xpath(run=run, table_selector=table_selector)

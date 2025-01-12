import pathlib
from itertools import chain, combinations
from typing import Any
from unittest.mock import patch, MagicMock, call, PropertyMock
from xml.etree import ElementTree

import pytest

from core.xc.xctrace.toc import ProcessEntry, TOC
from core.xc.xctrace.xml_parser import (
    XctraceXMLParser,
    table_xpath,
    table_number_xpath,
    table_schemas_xpath,
    Schema,
)


@pytest.fixture
def mock_xml_element_root():
    yield MagicMock(spec=ElementTree.Element)


@pytest.fixture
def mock_xml_element_tree(mock_xml_element_root):
    mock = MagicMock(spec=ElementTree.ElementTree)
    mock.getroot.return_value = mock_xml_element_root
    yield mock


@pytest.fixture
def mock_xml_element_tree_parser(mock_xml_element_tree):
    with patch("core.xc.xctrace.xml_parser.ElementTree") as mock:
        mock.parse.return_value = mock_xml_element_tree

        yield mock


@pytest.fixture
def mock_toc():
    yield MagicMock(spec=TOC)


@pytest.fixture
def mock_path():
    yield MagicMock(spec=pathlib.Path)


@pytest.fixture
def parser(mock_path, mock_toc, mock_xml_element_tree_parser):
    yield XctraceXMLParser(mock_path, mock_toc)


class TestXctraceXMLParser:
    def test_init(
        self,
        mock_xml_element_tree_parser,
        mock_xml_element_tree,
        mock_xml_element_root,
        mock_path,
        mock_toc,
    ):
        with (
            patch.object(
                XctraceXMLParser,
                "_XctraceXMLParser__relevant_tag_xpaths",
                new_callable=PropertyMock(return_value=["test"]),
            ) as mock_relevant_tag_xpaths,
            patch.object(XctraceXMLParser, "_cache_refs") as mock_cache_refs,
        ):
            parser = XctraceXMLParser(mock_path, mock_toc)

            assert parser._XctraceXMLParser__tree == mock_xml_element_tree
            mock_xml_element_tree_parser.parse.assert_called_once_with(
                mock_path.absolute().as_posix()
            )
            assert parser._XctraceXMLParser__root == mock_xml_element_root
            assert parser._XctraceXMLParser__toc == mock_toc
            assert parser._XctraceXMLParser__cache_map == {}
            mock_cache_refs.assert_called_once_with(mock_relevant_tag_xpaths)

    def test_parse_sysmon_for_target(self, parser, mock_xml_element_root):
        """
        GIVEN: A parser instance
        AND: An XML element root.

        WHEN: The parse_sysmon_for_target method is called with a run number and a process entry.

        AND: The method should call _get_table_number_for_schema with the correct arguments.
        THEN: The method should call _get_rows with the correct arguments.
        AND: The method should call _extract_sysmon with the result of _get_rows.
        """
        process_entry_mock = MagicMock(spec=ProcessEntry)
        process_entry_mock.name = "any_name"
        process_entry_mock.pid = 1

        with (
            patch.object(parser, "_get_rows") as mock_get_rows,
            patch.object(parser, "_extract_sysmon") as mock_extract_sysmon,
            patch.object(
                parser, "_get_table_number_for_schema", return_value=1
            ) as mock_get_table_number_for_schema,
        ):
            mock_get_rows.return_value = MagicMock()

            parser.parse_sysmon_for_target(1, process_entry_mock)

            mock_get_rows.assert_called_once_with(
                mock_xml_element_root,
                node_xpath_attrib="//trace-toc[1]/run[1]/data[1]/table[1]",
                row_selector='process[starts-with(@fmt, "any_name") or ends-with(@fmt, "(1)")]',
            )
            mock_extract_sysmon.assert_called_once_with(mock_get_rows.return_value)
            mock_get_table_number_for_schema.assert_called_once_with(
                1, Schema.SYSMON_PROCESS
            )

    def test_parse_core_animation(self, parser, mock_xml_element_root):
        """
        GIVEN: A parser instance
        AND: An XML element root.

        WHEN: The parse_core_animation method is called with a run number.

        AND: The method should call _get_table_number_for_schema with the correct arguments.
        THEN: The method should call _get_rows with the correct arguments.
        AND: The method should call _extract_core_animation with the result of _get_rows.
        """
        with (
            patch.object(
                parser, "_get_table_number_for_schema", return_value=2
            ) as mock_get_table_number_for_schema,
            patch.object(parser, "_get_rows") as mock_get_rows,
            patch.object(
                parser, "_extract_core_animation"
            ) as mock_extract_core_animation,
        ):
            mock_get_rows.return_value = MagicMock()

            parser.parse_core_animation(1)

            mock_get_rows.assert_called_once_with(
                mock_xml_element_root,
                node_xpath_attrib="//trace-toc[1]/run[1]/data[1]/table[2]",
            )
            mock_extract_core_animation.assert_called_once_with(
                mock_get_rows.return_value
            )
            mock_get_table_number_for_schema.assert_called_once_with(
                1, Schema.CORE_ANIMATION_FPS_ESTIMATE
            )

    def test_parse_stdout_err(self, parser, mock_xml_element_root):
        """
        GIVEN: A parser instance
        AND: An XML element root.

        WHEN: The parse_stdout_err method is called with a run number.

        AND: The method should call _get_table_number_for_schema with the correct arguments.
        THEN: The method should call _get_rows with the correct arguments.
        AND: The method should call _extract_stdout_err with the result of _get_rows.
        """
        with (
            patch.object(
                parser, "_get_table_number_for_schema", return_value=3
            ) as mock_get_table_number_for_schema,
            patch.object(parser, "_get_rows") as mock_get_rows,
            patch.object(parser, "_extract_stdout_err") as mock_extract_stdout_err,
        ):
            mock_get_rows.return_value = MagicMock()

            parser.parse_stdout_err(1)

            mock_get_rows.assert_called_once_with(
                mock_xml_element_root,
                node_xpath_attrib="//trace-toc[1]/run[1]/data[1]/table[3]",
            )
            mock_extract_stdout_err.assert_called_once_with(mock_get_rows.return_value)
            mock_get_table_number_for_schema.assert_called_once_with(
                1, Schema.STDOUTERR_OUTPUT
            )

    @staticmethod
    def _generate_combinations(values: list[Any]):
        return list(
            chain.from_iterable(combinations(values, r) for r in range(len(values) + 1))
        )

    @pytest.mark.parametrize(
        "schema_names_in_toc",
        _generate_combinations(
            ["sysmon-process", "stdouterr-output", "core-animation-fps-estimate"]
        ),
    )
    def test_parse_multiple(self, parser, mock_toc, schema_names_in_toc):
        """
        GIVEN: A parser instance
        AND: A TOC instance with a run that contains data tables with the given schema names.

        WHEN: The parse_multiple method is called with the run number.

        THEN: The method should call the correct parsing methods.
        AND: The method should return a dictionary with the correct schema names as keys and values.
        """
        mock_toc.runs = [
            MagicMock(
                data=[
                    MagicMock(schema_name=schema_name)
                    for schema_name in schema_names_in_toc
                ]
            ),
        ]

        process_entry_mock = MagicMock(spec=ProcessEntry)

        with (
            patch.object(
                parser, "parse_sysmon_for_target"
            ) as mock_parse_sysmon_for_target,
            patch.object(parser, "parse_stdout_err") as mock_parse_stdout_err,
            patch.object(parser, "parse_core_animation") as mock_parse_core_animation,
        ):
            mock_parse_sysmon_for_target.return_value = MagicMock()
            mock_parse_stdout_err.return_value = MagicMock()
            mock_parse_core_animation.return_value = MagicMock()

            data = parser.parse_multiple(1, process_entry_mock)

            if Schema.SYSMON_PROCESS in schema_names_in_toc:
                mock_parse_sysmon_for_target.assert_called_once_with(
                    1, process_entry_mock
                )
                assert (
                    data[Schema.SYSMON_PROCESS]
                    == mock_parse_sysmon_for_target.return_value
                )
            else:
                mock_parse_sysmon_for_target.assert_not_called()
                assert data[Schema.SYSMON_PROCESS] is None
            if Schema.STDOUTERR_OUTPUT in schema_names_in_toc:
                mock_parse_stdout_err.assert_called_once_with(1)
                assert (
                    data[Schema.STDOUTERR_OUTPUT] == mock_parse_stdout_err.return_value
                )
            else:
                mock_parse_stdout_err.assert_not_called()
                assert data[Schema.STDOUTERR_OUTPUT] is None
            if Schema.CORE_ANIMATION_FPS_ESTIMATE in schema_names_in_toc:
                mock_parse_core_animation.assert_called_once_with(1)
                assert (
                    data[Schema.CORE_ANIMATION_FPS_ESTIMATE]
                    == mock_parse_core_animation.return_value
                )
            else:
                mock_parse_core_animation.assert_not_called()
                assert data[Schema.CORE_ANIMATION_FPS_ESTIMATE] is None

    def test_cache_elements(self, parser):
        """
        GIVEN: A parser instance
        AND: An XML element with two children, one with an "id" attribute and the other with a "ref" attribute.

        WHEN: The cache_elements method is called with the XML element and a xpath.

        THEN: The cache_map attribute should contain the element with the "id" attribute.
        AND: The findall method should be called with the xpath.
        """
        mock_element = MagicMock(spec=ElementTree.Element)

        mock_id_element = MagicMock(spec=ElementTree.Element)
        mock_id_element.attrib = {
            "id": "test",
        }

        mock_ref_element = MagicMock(spec=ElementTree.Element)
        mock_ref_element.attrib = {
            "ref": "test",
        }

        mock_element.findall.return_value = [
            mock_id_element,
            mock_ref_element,
        ]

        parser._cache_elements(element=mock_element, xpath="any_xpath")

        assert parser._XctraceXMLParser__cache_map == {
            "test": mock_id_element,
        }
        mock_element.findall.assert_called_once_with("any_xpath")

    def test_cache_refs(self, parser):
        """
        GIVEN: A parser instance
        AND: A list of paths to search for elements.

        WHEN: The cache_refs method is called.

        THEN: The cache_elements method should be called for each path.
        """
        paths = [
            ".//path1",
            ".//path2",
        ]

        with patch.object(parser, "_cache_elements") as mock_cache_elements:
            parser._cache_refs(xpaths=paths)

            mock_cache_elements.assert_has_calls(
                [
                    call(parser._XctraceXMLParser__root, ".//path1[@id]"),
                    call(parser._XctraceXMLParser__root, ".//path2[@id]"),
                ],
                any_order=True,
            )

    def test_get_cached_element_cache_lookup(self, parser):
        """
        GIVEN: A parser instance
        AND: A cached element with the given id.
        AND: An element that references the cached element.
        AND: A parent element that contains the element

        WHEN: The get_cached_element method is called with an element that references the cached element.

        THEN: The method should return the cached element.
        AND: The cache_map should be accessed.
        """
        mock_element = MagicMock(spec=ElementTree.Element)

        element_to_search_for = MagicMock(
            spec=ElementTree.Element, attrib={"ref": "test"}
        )

        element_to_search_in = MagicMock(spec=ElementTree.Element)
        element_to_search_in.findall.return_value = [element_to_search_for]

        with patch.object(
            parser, "_XctraceXMLParser__cache_map"
        ) as mock_cache_elements:
            mock_cache_elements.__getitem__.side_effect = {
                "test": mock_element
            }.__getitem__

            assert (
                parser._get_cached_element(element_to_search_in, "any_xpath")
                == mock_element
            )
            mock_cache_elements.__getitem__.assert_called_once_with("test")

    def test_get_cached_element_no_cache_lookup(self, parser):
        """
        GIVEN: A parser instance
        AND: An element that has an id attribute.
        AND: A parent element that contains the element.

        WHEN: The get_cached_element method is called with the element.

        THEN: The method should return the element.
        AND: The cache_map should not be accessed.
        """
        mock_element = MagicMock(spec=ElementTree.Element, attrib={"id": "test"})

        element_to_search_in = MagicMock(spec=ElementTree.Element)
        element_to_search_in.findall.return_value = [mock_element]

        with patch.object(
            parser, "_XctraceXMLParser__cache_map"
        ) as mock_cache_elements:
            assert (
                parser._get_cached_element(element_to_search_in, "any_xpath")
                == mock_element
            )
            mock_cache_elements.__getitem__.assert_not_called()

    def test_get_cached_element_no_elements_found(self, parser):
        """
        GIVEN: A parser instance
        AND: A parent element that contains no elements.

        WHEN: The get_cached_element method is called with the parent element.

        THEN: The method should raise a ValueError.
        """
        element_to_search_in = MagicMock(spec=ElementTree.Element)
        element_to_search_in.findall.return_value = []

        with pytest.raises(ValueError):
            parser._get_cached_element(element_to_search_in, "any_xpath")

    def test_get_cached_element_multiple_elements_found(self, parser):
        """
        GIVEN: A parser instance
        AND: A parent element that contains multiple elements.

        WHEN: The get_cached_element method is called with the parent element.

        THEN: The method should raise a ValueError.
        """
        element_to_search_in = MagicMock(spec=ElementTree.Element)
        element_to_search_in.findall.return_value = [
            MagicMock(spec=ElementTree.Element),
            MagicMock(spec=ElementTree.Element),
        ]

        with pytest.raises(ValueError):
            parser._get_cached_element(element_to_search_in, "any_xpath")

    def test_get_table_number_for_schema(self, parser, mock_toc):
        """
        GIVEN: A parser instance
        AND: A TOC instance with a run that contains two data tables with different schema names.
        AND: A run number.
        AND: A schema.

        WHEN: The get_table_number_for_schema method is called with the run number and schema.

        THEN: The method should return the correct table number.
        AND: The method should raise a ValueError if the schema is not found.
        AND: The method should raise an IndexError if the run number is out of bounds.
        """
        mock_toc.runs = [
            MagicMock(
                data=[
                    MagicMock(schema_name="sysmon-process"),
                    MagicMock(schema_name="stdouterr-output"),
                ]
            ),
        ]

        assert parser._get_table_number_for_schema(1, Schema.SYSMON_PROCESS) == 1
        assert parser._get_table_number_for_schema(1, Schema.STDOUTERR_OUTPUT) == 2
        with pytest.raises(ValueError):
            parser._get_table_number_for_schema(1, Schema.CORE_ANIMATION_FPS_ESTIMATE)
        with pytest.raises(IndexError):
            parser._get_table_number_for_schema(2, Schema.SYSMON_PROCESS)

    @pytest.mark.xfail
    def test_extract_sysmon(self, parser):
        parser._extract_sysmon([])

    @pytest.mark.xfail
    def test_extract_core_animation(self, parser):
        parser._extract_core_animation([])

    @pytest.mark.xfail
    def test_extract_stdout_err(self, parser):
        parser._extract_stdout_err([])

    @pytest.mark.parametrize(
        "row_selector, expected",
        [
            ('@some="attr"', './/node[@xpath="test_xpath"]/row[@some="attr"]'),
            (None, './/node[@xpath="test_xpath"]/row'),
        ],
    )
    def test_get_rows_find_all_call(self, parser, row_selector, expected):
        """
        GIVEN: A parser instance
        AND: An XML element root.
        AND: An xpath identifying the node to search for.

        WHEN: The get_rows method is called with the XML element root and the xpath.

        THEN: The method should call the findall method with the xpath.
        """
        element_mock = MagicMock(spec=ElementTree.Element)
        xpath = "test_xpath"

        parser._get_rows(element_mock, xpath, row_selector=row_selector)
        element_mock.findall.assert_called_once_with(expected)

    def test_get_rows(self, parser):
        """
        GIVEN: A parser instance
        AND: An XML element root.
        AND: A XML element (node) in the root element, containing two rows.
        AND: An xpath identifying the node to search for.

        WHEN: The get_rows method is called with the XML element root and the xpath.

        THEN: The method should return the correct rows.
        """
        element = ElementTree.Element("root")
        xpath = "test_xpath"
        node_element = ElementTree.SubElement(element, "node", attrib={"xpath": xpath})

        row_1 = ElementTree.SubElement(node_element, "row")
        row_2 = ElementTree.SubElement(node_element, "row", attrib={"some": "attr"})

        rows = parser._get_rows(element, xpath)
        assert rows == [row_1, row_2]

        rows = parser._get_rows(element, xpath, row_selector='@some="attr"')
        assert rows == [row_2]

        rows = parser._get_rows(element, "non_existent_xpath")
        assert rows == []


class TestTableXpath:
    @pytest.mark.parametrize(
        "run, selector, expected",
        [
            (1, "test", "//trace-toc[1]/run[1]/data[1]/table[test]"),
            (2, "test2", "//trace-toc[1]/run[2]/data[1]/table[test2]"),
            (10, "test3", "//trace-toc[1]/run[10]/data[1]/table[test3]"),
        ],
    )
    def test_table_xpath(self, run, selector, expected):
        """
        GIVEN: A run number and a table selector.

        WHEN: The table_xpath method is called with the run number and table selector.

        THEN: The method should return the correct xpath.
        """
        assert table_xpath(run=run, table_selector=selector) == expected

    @pytest.mark.parametrize(
        "run, table_number, expected",
        [
            (1, 1, "//trace-toc[1]/run[1]/data[1]/table[1]"),
            (2, 2, "//trace-toc[1]/run[2]/data[1]/table[2]"),
            (10, 3, "//trace-toc[1]/run[10]/data[1]/table[3]"),
        ],
    )
    def test_table_number_xpath(self, run, table_number, expected):
        """
        GIVEN: A run number and a table number.

        WHEN: The table_number_xpath method is called with the run number and table number.

        THEN: The method should return the correct xpath.
        """
        assert table_number_xpath(run=run, table_number=table_number) == expected

    @pytest.mark.parametrize(
        "run, schemas, expected",
        [
            (
                1,
                [Schema.SYSMON_PROCESS, Schema.STDOUTERR_OUTPUT],
                '//trace-toc[1]/run[1]/data[1]/table[@schema="sysmon-process" or @schema="stdouterr-output"]',
            ),
            (
                2,
                [Schema.CORE_ANIMATION_FPS_ESTIMATE],
                '//trace-toc[1]/run[2]/data[1]/table[@schema="core-animation-fps-estimate"]',
            ),
        ],
    )
    def test_table_schemas_xpath(self, run, schemas, expected):
        """
        GIVEN: A run number and a list of schema names.

        WHEN: The table_schemas_xpath method is called with the run number and list of schema names.

        THEN: The method should return the correct xpath.
        """
        assert table_schemas_xpath(run=run, schemas=schemas) == expected

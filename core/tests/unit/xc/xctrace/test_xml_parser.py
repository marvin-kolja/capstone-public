import pathlib
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
        with patch.object(
            XctraceXMLParser,
            "_XctraceXMLParser__relevant_tag_xpaths",
            new_callable=PropertyMock(return_value=["test"]),
        ) as mock_relevant_tag_xpaths, patch.object(
            XctraceXMLParser, "_cache_refs"
        ) as mock_cache_refs:
            parser = XctraceXMLParser(mock_path, mock_toc)

            assert parser._XctraceXMLParser__tree == mock_xml_element_tree
            mock_xml_element_tree_parser.parse.assert_called_once_with(
                mock_path.absolute().as_posix()
            )
            assert parser._XctraceXMLParser__root == mock_xml_element_root
            assert parser._XctraceXMLParser__toc == mock_toc
            assert parser._XctraceXMLParser__cache_map == {}
            mock_cache_refs.assert_called_once_with(mock_relevant_tag_xpaths)

    @pytest.mark.xfail
    def test_parse_sysmon_for_target(self, parser):
        process_entry_mock = MagicMock(spec=ProcessEntry)
        parser.parse_sysmon_for_target(1, process_entry_mock)

    @pytest.mark.xfail
    def test_parse_core_animation(self, parser):
        parser.parse_core_animation(1)

    @pytest.mark.xfail
    def test_parse_stdout_err(self, parser):
        parser.parse_stdout_err(1)

    @pytest.mark.xfail
    def test_parse_multiple(self, parser):
        parser.parse_multiple(1)

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

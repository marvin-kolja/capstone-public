import pathlib
from unittest.mock import patch, MagicMock
from xml.etree import ElementTree

import pytest

from core.xc.xctrace.toc import ProcessEntry, TOC
from core.xc.xctrace.xml_parser import XctraceXMLParser


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
        parser,
        mock_xml_element_tree_parser,
        mock_xml_element_tree,
        mock_xml_element_root,
        mock_path,
        mock_toc,
    ):
        assert parser._XctraceXMLParser__tree == mock_xml_element_tree
        mock_xml_element_tree_parser.parse.assert_called_once_with(
            mock_path.absolute().as_posix()
        )
        assert parser._XctraceXMLParser__root == mock_xml_element_root
        assert parser._XctraceXMLParser__toc == mock_toc
        assert parser._XctraceXMLParser__cache_map == {}

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

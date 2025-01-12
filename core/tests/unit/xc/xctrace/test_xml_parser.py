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
    mock.get_root.return_value = mock_xml_element_root
    yield mock


@pytest.fixture
def mock_xml_element_tree_parser(mock_xml_element_tree):
    with patch("core.xc.xctrace.xml_parser.ElementTree") as mock:
        mock.parse.return_value = mock_xml_element_tree

        yield mock


@pytest.fixture
def parser():
    toc_mock = MagicMock(spec=TOC)
    path_mock = MagicMock(spec=pathlib.Path)

    yield XctraceXMLParser(path_mock, toc_mock)


@pytest.mark.xfail
class TestXctraceXMLParser:

    def test_parse_sysmon_for_target(self, parser):
        process_entry_mock = MagicMock(spec=ProcessEntry)
        parser.parse_sysmon_for_target(1, process_entry_mock)

    def test_parse_core_animation(self, parser):
        parser.parse_core_animation(1)

    def test_parse_stdout_err(self, parser):
        parser.parse_stdout_err(1)

    def test_parse_multiple(self, parser):
        parser.parse_multiple(1)

import pathlib

import pytest

from core.xc.xctrace.toc import parse_toc_xml
from core.xc.xctrace.xml_parser import XctraceXMLParser


@pytest.fixture
def _test_data_dir():
    return pathlib.Path(__file__).parent / ".." / ".." / ".." / "test_data"


@pytest.fixture
def toc(_test_data_dir):
    return parse_toc_xml(_test_data_dir / "Example_trace_toc.xml")


@pytest.fixture
def parser(_test_data_dir, toc):
    return XctraceXMLParser(path=_test_data_dir / "Example_trace_data.xml", toc=toc)


class TestXMLParser:
    def test_parse_sysmon_for_target(self, parser, toc):
        """
        GIVEN: A parser and a TOC object

        WHEN: parse_sysmon_for_target is called

        THEN: The correct amount of sysmon data is returned
        AND: The first sysmon data is correct
        """
        toc_run = toc.runs[0]

        sysmon_data = parser.parse_sysmon_for_target(
            run=1, target_process=toc_run.info.target.process
        )
        assert len(sysmon_data) == 3
        assert sysmon_data[0].timestamp == 137338541
        assert sysmon_data[0].cpu is None
        assert sysmon_data[0].memory == 0.07830047607421875
        assert sysmon_data[0].resident_size == 0.046875
        assert sysmon_data[0].recently_died is False

    def test_parse_core_animation(self, parser):
        """
        GIVEN: A parser

        WHEN: parse_core_animation is called

        THEN: The correct amount of core animation data is returned
        AND: The first core animation data is correct
        """
        core_animation_data = parser.parse_core_animation(run=1)

        assert len(core_animation_data) == 3
        assert core_animation_data[0].timestamp == 0
        assert core_animation_data[0].fps == 0
        assert core_animation_data[0].gpu_utilization == 3

    def test_parse_stdouterr_output(self, parser):
        """
        GIVEN: A parser

        WHEN: parse_stdout_err is called

        THEN: The correct amount of stdouterr output data is returned
        AND: The first stdouterr output data is correct
        """
        stdouterr_output_data = parser.parse_stdout_err(run=1)

        assert len(stdouterr_output_data) == 3
        assert stdouterr_output_data[0].timestamp == 1192596333
        assert stdouterr_output_data[0].console_text == 'Appeared: "Home"'

import pathlib
from unittest import mock
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from core.xc.xctrace.toc import (
    parse_toc_xml,
    TOC,
    TOCRun,
    ProcessEntry,
    TOCDataTable,
    TOCRunInfo,
    TOCRunInfoTarget,
    TOCRunInfoSummary,
)


@pytest.fixture
def fake_trace_xml():
    return """<?xml version="1.0"?>
    <trace-toc>
        <run number="1">
            <info>
                <target>
                    <process name="name" pid="1" return-exit-status="0" termination-reason="reason" path="path"/>
                </target>
                <summary start-date="start" end-date="end" duration="1.0" end-reason="reason" instruments-version="version" template-name="template" recording-mode="mode" time-limit="limit"/>
            </info>
            <processes>
                <process name="name" pid="1" return-exit-status="0" termination-reason="reason" path="path"/>
            </processes>
            <data>
                <table schema="schema"/>
            </data>
        </run>
    </trace-toc>
    """


@pytest.fixture
def fake_toc():
    return TOC(
        runs=[
            TOCRun(
                processes=[
                    ProcessEntry(
                        name="name",
                        pid=1,
                        return_exit_status=0,
                        termination_reason="reason",
                        path="path",
                    )
                ],
                number=1,
                data=[TOCDataTable(schema_name="schema")],
                info=TOCRunInfo(
                    target=TOCRunInfoTarget(
                        process=ProcessEntry(
                            name="name",
                            pid=1,
                            return_exit_status=0,
                            termination_reason="reason",
                            path="path",
                        )
                    ),
                    summary=TOCRunInfoSummary(
                        start_date="start",
                        end_date="end",
                        duration=1.0,
                        end_reason="reason",
                        instruments_version="version",
                        template_name="template",
                        recording_mode="mode",
                        time_limit="limit",
                    ),
                ),
            )
        ]
    )


def test_parse_toc_xml(fake_trace_xml, fake_toc):
    """
    GIVEN: a valid TOC XML file

    WHEN: the file is parsed

    THEN: a TOC object is returned with the expected values
    """
    fake_path = pathlib.Path("mocked_toc.xml")

    opener = mock.mock_open(read_data=fake_trace_xml)

    def mocked_open(self, *args, **kwargs):
        return opener(self, *args, **kwargs)

    with mock.patch.object(pathlib.Path, "open", mocked_open):
        assert parse_toc_xml(fake_path) == fake_toc


def test_parse_toc_xml_invalid(fake_toc):
    """
    GIVEN: an invalid TOC XML file

    WHEN: the file is parsed

    THEN: a ValidationError is raised
    """
    fake_path = pathlib.Path("mocked_toc.xml")

    opener = mock.mock_open(read_data="<xml></xml>")

    def mocked_open(self, *args, **kwargs):
        return opener(self, *args, **kwargs)

    with mock.patch.object(pathlib.Path, "open", mocked_open):
        with pytest.raises(ValidationError):
            assert parse_toc_xml(fake_path) == fake_toc


class TestTOCRun:
    def test_restructure_list_fields_dict(self):
        """
        GIVEN: processes field is a dictionary
        AND: data field is a dictionary

        WHEN: the `restructure_list_fields` method is called

        THEN: it should correctly restructure the `processes` and `data` fields to lists
        """
        info_mock = MagicMock(spec=dict)
        process_mock = MagicMock(spec=dict)
        table_mock = MagicMock(spec=dict)

        data = {
            "processes": {"process": process_mock},
            "data": {"table": table_mock},
            "info": info_mock,
        }

        restructured_data = TOCRun.model_validate(data)

        assert restructured_data["processes"] == [process_mock]
        assert restructured_data["data"] == [table_mock]

    def test_restructure_list_fields_list(self):
        """
        GIVEN: processes.process field is a list
        AND: data.table field is a list

        WHEN: the `restructure_list_fields` method is called

        THEN: it should correctly restructure the `processes` and `data` fields to lists
        """
        info_mock = MagicMock(spec=dict)
        process_mock = MagicMock(spec=dict)
        table_mock = MagicMock(spec=dict)

        data = {
            "processes": {"process": [process_mock]},
            "data": {"table": [table_mock]},
            "info": info_mock,
        }

        restructured_data = TOCRun.model_validate(data)

        assert restructured_data["processes"] == [process_mock]
        assert restructured_data["data"] == [table_mock]


class TestTOC:
    def test_validate(self):
        """
        GIVEN: a TOC object with valid fields

        WHEN: the object is validated

        THEN: no exception should be raised
        """
        mock_run = MagicMock(spec=TOCRun)
        TOC.model_validate({"runs": [mock_run]})

    def test_restructure_runs_dict(self):
        """
        GIVEN: trace-toc.run field is a dictionary

        WHEN: the TOC is validated

        THEN: it should correctly restructure the nested field to a list and map it to the `runs` field
        """
        mock_run = {
            "processes": [MagicMock(spec=ProcessEntry)],
            "data": [MagicMock(spec=TOCDataTable)],
            "info": MagicMock(spec=TOCRunInfo),
            "number": 1,
        }

        data = {
            "trace-toc": {"run": mock_run},
        }

        toc = TOC.model_validate(data)

        assert toc.runs[0].processes == mock_run["processes"]
        assert toc.runs[0].data == mock_run["data"]
        assert toc.runs[0].info == mock_run["info"]
        assert toc.runs[0].number == mock_run["number"]

    def test_restructure_runs_list(self):
        """
        GIVEN: a dict with trace-toc.run field as a list

        WHEN: the TOC is validated

        THEN: it should correctly map the nested field to the `runs` field
        """
        mock_run_dict = {
            "processes": [MagicMock(spec=ProcessEntry)],
            "data": [MagicMock(spec=TOCDataTable)],
            "info": MagicMock(spec=TOCRunInfo),
            "number": 1,
        }

        data = {
            "trace-toc": {"run": [mock_run_dict]},
        }

        toc = TOC.model_validate(data)

        assert toc.runs[0].processes == mock_run_dict["processes"]
        assert toc.runs[0].data == mock_run_dict["data"]
        assert toc.runs[0].info == mock_run_dict["info"]
        assert toc.runs[0].number == mock_run_dict["number"]

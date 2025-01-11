import pathlib
from unittest import mock

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

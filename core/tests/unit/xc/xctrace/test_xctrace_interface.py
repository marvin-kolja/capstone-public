import pathlib
import signal
from unittest import mock
from unittest.mock import MagicMock

import pytest

from core.xc.commands.xctrace_command import Instrument, XctraceCommand
from core.xc.xctrace.xctrace_interface import Xctrace


@pytest.fixture
def mock_async_run_process():
    with mock.patch(
        "core.xc.xctrace.xctrace_interface.async_run_process"
    ) as mock_async_run_process:
        yield mock_async_run_process


@pytest.fixture
def mock_xctrace_command():
    with mock.patch(
        "core.xc.xctrace.xctrace_interface.XctraceCommand"
    ) as mock_xctrace_command:
        yield mock_xctrace_command


class TestXctraceInterface:
    @pytest.mark.asyncio
    async def test_record_launch(self, mock_xctrace_command, mock_async_run_process):
        """
        GIVEN: A path to save the trace file, a device, a list of instruments, an app to launch, and a boolean to append the trace

        WHEN: The trace is recorded by launching an app

        THEN: The underlying record_command function is called with the parameters
        AND: The async_run_process function is called with the command instance
        """
        mock_command_instance = MagicMock(spec=XctraceCommand)
        mock_xctrace_command.record_command.return_value = mock_command_instance

        data_kwargs = {
            "trace_path": "trace_path",
            "device": "device",
            "instruments": [Instrument.activity_monitor],
            "app_to_launch": "app_to_launch",
            "append_trace": False,
        }

        await Xctrace.record_launch(**data_kwargs)

        mock_xctrace_command.record_command.assert_called_once_with(
            instruments=[Instrument.activity_monitor],
            output_path="trace_path",
            device="device",
            append=False,
            attach=None,
            launch="app_to_launch",
        )
        mock_async_run_process.assert_awaited_once_with(
            mock_command_instance, signal_on_cancel=signal.SIGINT
        )

    @pytest.mark.asyncio
    async def test_record_attach(self, mock_xctrace_command, mock_async_run_process):
        """
        GIVEN: A path to save the trace file, a device, a list of instruments, a PID, and a boolean to append the trace

        WHEN: The trace is recorded by attaching to a process

        THEN: The underlying record_command function is called with the parameters
        AND: The async_run_process function is called with the command instance
        """
        mock_command_instance = MagicMock(spec=XctraceCommand)
        mock_xctrace_command.record_command.return_value = mock_command_instance

        data_kwargs = {
            "trace_path": "trace_path",
            "device": "device",
            "instruments": [Instrument.activity_monitor],
            "pid": 123,
            "append_trace": False,
        }

        await Xctrace.record_attach(**data_kwargs)

        mock_xctrace_command.record_command.assert_called_once_with(
            instruments=[Instrument.activity_monitor],
            output_path="trace_path",
            device="device",
            append=False,
            attach=123,
            launch=None,
        )
        mock_async_run_process.assert_awaited_once_with(
            mock_command_instance, signal_on_cancel=signal.SIGINT
        )

    @pytest.mark.asyncio
    async def test_export_toc(self, mock_xctrace_command, mock_async_run_process):
        """
        GIVEN: A path to a trace file and a path to save the TOC

        WHEN: The TOC is exported

        THEN: The underlying export_toc_command function is called with the paths
        AND: The async_run_process function is called with the command instance
        """
        mock_command_instance = MagicMock(spec=XctraceCommand)
        mock_xctrace_command.export_toc_command.return_value = mock_command_instance

        data_kwargs = {
            "trace_path": "input_path",
            "toc_path": "output_path",
        }

        await Xctrace.export_toc(**data_kwargs)

        mock_xctrace_command.export_toc_command.assert_called_once_with(
            input_path="input_path", output_path="output_path"
        )
        mock_async_run_process.assert_awaited_once_with(mock_command_instance)

    @pytest.mark.asyncio
    async def test_export_data(self, mock_xctrace_command, mock_async_run_process):
        """
        GIVEN: A path to a trace file, a path to save the data, and a xpath

        WHEN: The data is exported

        THEN: The underlying export_data_command function is called with the paths and xpath
        AND: The async_run_process function is called with the command instance
        """
        mock_command_instance = MagicMock(spec=XctraceCommand)
        mock_xctrace_command.export_data_command.return_value = mock_command_instance

        data_kwargs = {
            "trace_path": "input_path",
            "data_path": "output_path",
            "xpath": "xpath",
        }

        await Xctrace.export_data(**data_kwargs)

        mock_xctrace_command.export_data_command.assert_called_once_with(
            input_path="input_path", output_path="output_path", xpath="xpath"
        )
        mock_async_run_process.assert_awaited_once_with(mock_command_instance)

    def test_parse_toc_xml(self):
        """
        GIVEN: A path to a TOC XML file

        WHEN: The TOC XML file is parsed

        THEN: The underlying parse_toc_xml function is called with the path
        """
        path = MagicMock(spec=str)

        with mock.patch(
            "core.xc.xctrace.xctrace_interface.parse_toc_xml"
        ) as mock_toc_parser:
            Xctrace.parse_toc_xml(path)

            mock_toc_parser.assert_called_once_with(pathlib.Path(path))

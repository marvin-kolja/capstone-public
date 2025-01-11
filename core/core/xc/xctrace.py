import logging
import signal
from typing import Optional

from core.subprocess import async_run_process
from core.xc.commands.xctrace_command import Instrument, XctraceCommand

logger = logging.getLogger(__name__)


class Xctrace:
    @staticmethod
    async def record_launch(
        trace_path: str,
        device: str,
        instruments: list[Instrument],
        app_to_launch: str,
        append_trace: Optional[bool] = False,
    ):
        """
        Records a trace file by launching an app on a device and recording the trace using the specified instruments

        :param trace_path: The path to save the trace file
        :param device: The device to record the trace on
        :param instruments: The instruments to record
        :param app_to_launch: The app to launch
        :param append_trace: Whether to append the trace to an existing trace file
        """
        logger.debug(
            f"Recording trace using {instruments} for {app_to_launch} on {device} to {trace_path}"
        )

        command = XctraceCommand.record_command(
            instruments=instruments,
            output_path=trace_path,
            device=device,
            append=append_trace,
            attach=None,
            launch=app_to_launch,
        )

        await async_run_process(command, signal_on_cancel=signal.SIGINT)

    @staticmethod
    async def record_attach(
        trace_path: str,
        device: str,
        instruments: list[Instrument],
        pid: int,
        append_trace: Optional[bool] = False,
    ):
        """
        Records a trace file by attaching to a process on a device and recording the trace using the specified
        instruments

        :param trace_path: The path to save the trace file
        :param device: The device to record the trace on
        :param instruments: The instruments to record
        :param pid: The process id to attach to
        :param append_trace: Whether to append the trace to an existing trace file
        """
        logger.debug(
            f"Recording trace using {instruments} for {pid} on {device} to {trace_path}"
        )

        command = XctraceCommand.record_command(
            instruments=instruments,
            output_path=trace_path,
            device=device,
            append=append_trace,
            attach=pid,
            launch=None,
        )

        await async_run_process(command, signal_on_cancel=signal.SIGINT)

    @staticmethod
    async def export_toc(trace_path: str, toc_path: str):
        """
        Exports the Table of Contents from a trace file to an output file in XML format

        :param trace_path: The path to the trace file
        :param toc_path: The path to the file to save the Table of Contents to
        """
        logger.debug(f"Exporting toc from {trace_path} to {toc_path}")

        command = XctraceCommand.export_toc_command(
            input_path=trace_path,
            output_path=toc_path,
        )

        await async_run_process(command)

    @staticmethod
    async def export_data(trace_path: str, data_path: str, xpath: str):
        """
        Exports data from a trace file to an output file in XML format using the specified XPath

        The XPath should be in the following format
        ``'/trace-toc/run[1]/data/table[@schema="sysmon-process"]'``. ``'run[1]'`` selects the run to export data from.
        Starts from 1. ``'table[@schema="sysmon-process"]'`` selects the data to export from the run by providing the
        schema name. You can also select multiple schemas by separating them with an `or` operator like so:
        ``'table[@schema="sysmon-process" or @schema="stdouterr-output"]'``

        :param trace_path: The path to the trace file
        :param data_path: The path to the file to save the data to
        :param xpath: The XPath to use to select the data to export
        """
        logger.debug(f"Exporting data from {trace_path} to {data_path}")

        command = XctraceCommand.export_data_command(
            input_path=trace_path,
            output_path=data_path,
            xpath=xpath,
        )

        await async_run_process(command)

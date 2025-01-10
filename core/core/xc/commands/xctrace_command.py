from enum import StrEnum
from typing import Optional, Literal

from core.subprocesses.process import ProcessCommand, CommandError


class Instrument(StrEnum):
    """
    The available instruments for recording traces with xctrace.

    Extracted from the output of `xctrace list instruments`.
    """

    activity_monitor = "Activity Monitor"
    core_animation_fps = "Core Animation FPS"
    stdout_stderr = "stdout/stderr"


class XctraceCommand(ProcessCommand):
    """
    A command parser to interact with the xctrace command.
    """

    def __init__(
        self,
        action: Literal["record", "export"],
        output_path: str,
        instruments: Optional[list[Instrument]] = None,
        device: Optional[str] = None,
        append: Optional[bool] = None,
        attach: Optional[int] = None,
        launch: Optional[str] = None,
        input_path: Optional[str] = None,
        xpath: Optional[str] = None,
        toc: Optional[bool] = None,
    ):
        """
        Initializes the xctrace command.


        :param action: The action to perform.
        :param output_path: The output path where the results will be saved.

        :param instruments: The instruments to record. If recording, at least one instrument is required.
        :param device: The device to use for recording. Name or UDID.
        :param append: If the recording should be appended to the existing trace file specified by the `output_path`.
        :param attach: The process ID to attach to for recording.
        :param launch: The application to launch for recording. Bundle identifier or path ("BundlePath")
            to the app on the device.


        :param input_path: The input path to the trace file to export.
        :param xpath: The XPath to the data to export.
        :param toc: If the table of contents should be exported.
        """
        self.action = action
        self.output = output_path

        # Record options
        self.instruments = instruments
        self.device = device
        self.append = append
        self.attach = attach
        self.launch = launch

        # Export options
        self.input = input_path
        self.xpath = xpath
        self.toc = toc

    def parse(self) -> list[str]:
        parsed_command: list[str] = ["xctrace", self.action, "--output", self.output]

        if self.action == "record":
            if self.instruments is not None:
                if len(self.instruments) == 0:
                    raise CommandError(
                        "At least one instrument is required for recording"
                    )
                for instrument in self.instruments:
                    parsed_command.extend(["--instrument", instrument])
            if self.device is not None:
                parsed_command.extend(["--device", self.device])
            if self.append:
                parsed_command.append("--append")
            if self.attach is not None:
                parsed_command.extend(["--attach", str(self.attach)])
            if self.launch is not None:
                parsed_command.extend(["--launch", self.launch])
        elif self.action == "export":
            if self.input is not None:
                parsed_command.extend(["--input", self.input])
            if self.xpath is not None:
                parsed_command.extend(["--xpath", self.xpath])
            if self.toc:
                parsed_command.append("--toc")
        else:
            raise CommandError(f"Unknown action: {self.action}")

        return parsed_command

    @classmethod
    def record_command(
        cls,
        instruments: list[Instrument],
        output_path: str,
        device: str,
        append: bool = False,
        attach: Optional[int] = None,
        launch: Optional[str] = None,
    ):
        if (attach is None) and (launch is None):
            raise CommandError("Either attach or launch is required for record command")
        if attach is True and (launch is not None):
            raise CommandError(
                "Either attach or launch is required for record command, not both"
            )

        return cls(
            "record",
            output_path,
            instruments=instruments,
            device=device,
            append=append,
            attach=attach,
            launch=launch,
        )

    @classmethod
    def export_toc_command(cls, input_path: str, output_path: str):
        """
        Creates an export command to export the table of contents of a trace file.
        """
        return cls("export", output_path, input_path=input_path, toc=True)

    @classmethod
    def export_data_command(cls, input_path: str, output_path: str, xpath: str):
        """
        Creates an export command to export data from a trace file using an XPath.
        """
        return cls("export", output_path, input_path=input_path, xpath=xpath)

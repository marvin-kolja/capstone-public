import pytest

from core.subprocesses.process import CommandError
from core.xc.commands.xctrace_command import XctraceCommand, Instrument
from tests.conftest import fake_udid


class TestXctraceCommand:
    """
    Tests for the xctrace command
    """

    def test_record_command(self, fake_udid):
        """
        GIVEN: A XctraceCommand class

        WHEN: calling `record_command`
        AND: then calling `parse` on the returned command

        THEN: The correct list of strings should be returned
        """
        command = XctraceCommand.record_command(
            instruments=[Instrument.activity_monitor],
            output_path="/tmp/output.trace",
            device=fake_udid,
            append=False,
            attach=None,
            launch="com.example.app",
        )

        parsed_command = command.parse()

        assert parsed_command == [
            "xctrace",
            "record",
            "--output",
            "/tmp/output.trace",
            "--instrument",
            Instrument.activity_monitor,
            "--device",
            fake_udid,
            "--launch",
            "com.example.app",
        ]

    def test_record_command_conflicting_options(self, fake_udid):
        """
        GIVEN: A XctraceCommand class

        WHEN: calling `record_command` with conflicting options

        THEN: A CommandError should be raised
        """
        with pytest.raises(CommandError):
            XctraceCommand.record_command(
                instruments=[Instrument.activity_monitor],
                output_path="/tmp/output.trace",
                device=fake_udid,
                append=False,
                attach=True,
                launch="com.example.app",
            )

    def test_record_command_missing_required_choice_options(self, fake_udid):
        """
        GIVEN: A XctraceCommand class

        WHEN: calling `record_command` with missing required choice options

        THEN: A CommandError should be raised
        """
        with pytest.raises(CommandError):
            XctraceCommand.record_command(
                instruments=[],
                output_path="/tmp/output.trace",
                device=fake_udid,
                append=False,
                # Missing required choice options
                attach=None,
                launch=None,
            )

    def test_export_toc_command(self):
        """
        GIVEN: A XctraceCommand class

        WHEN: calling `export_toc_command`
        AND: then calling `parse` on the returned command

        THEN: The correct list of strings should be returned
        """
        command = XctraceCommand.export_toc_command(
            input_path="/tmp/input.trace",
            output_path="/tmp/toc.xml",
        )

        parsed_command = command.parse()

        assert parsed_command == [
            "xctrace",
            "export",
            "--output",
            "/tmp/toc.xml",
            "--input",
            "/tmp/input.trace",
            "--toc",
        ]

    def test_export_data_command(self):
        """
        GIVEN: A XctraceCommand class

        WHEN: calling `export_data_command`
        AND: then calling `parse` on the returned command

        THEN: The correct list of strings should be returned
        """
        command = XctraceCommand.export_data_command(
            input_path="/tmp/input.trace",
            output_path="/tmp/data.xml",
            xpath='/trace-toc/run[@number="1"]/data/table[@schema="sysmon-process"]',
        )

        parsed_command = command.parse()

        assert parsed_command == [
            "xctrace",
            "export",
            "--output",
            "/tmp/data.xml",
            "--input",
            "/tmp/input.trace",
            "--xpath",
            '/trace-toc/run[@number="1"]/data/table[@schema="sysmon-process"]',
        ]

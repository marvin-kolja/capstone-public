import inspect
from unittest.mock import MagicMock

import pytest

from core.subprocesses.process import CommandError
from core.subprocesses.xcodebuild_command import (
    XcodebuildOptions,
    XcodebuildOption,
    XcodebuildOptionWithValue,
    XcodebuildCommand,
    Destination,
    XcodebuildTestCommand,
    IOSDestination,
    XcodebuildTestEnumerationCommand,
    XcodebuildBuildCommand,
    XcodebuildListCommand,
    XcodebuildShowTestPlansCommand,
)


def xcodebuild_options_attributes():
    attributes = []

    for attr_name in dir(XcodebuildOptions):
        if attr_name.startswith("__"):
            # Ignore pythons private attributes
            continue
        if attr_name.startswith("_XcodebuildOptions__"):
            # Ignore user defined private attributes
            continue
        attr = getattr(XcodebuildOptions, attr_name)
        attributes.append(attr)

    return attributes


@pytest.mark.parametrize("attr", xcodebuild_options_attributes())
class TestXcodebuildOptions:
    def test_all_methods_are_xcodebuild_option_decorated(self, attr):
        """
        GIVEN: A `XcodebuildOptions` attribute

        THEN: The attribute must be a callable
        AND: Must be decorated with `@xcodebuild_option`.
        """
        assert callable(attr)
        assert hasattr(attr, "__xcodebuild_option__")

    def test_all_methods_signature(self, attr):
        """
        GIVEN: A `XcodebuildOptions` attribute

        WHEN: checking getting the signature on that attribute

        THEN: The only param name must be "value"
        OR: There should be no param
        """
        params_sig = inspect.signature(attr).parameters

        for param_name in params_sig.keys():
            assert param_name == "value"

    def test_returned_value_is_correct_xcodebuild_option(self, attr):
        """
        GIVEN: A `XcodebuildOptions` attribute

        WHEN: Calling the attribute

        THEN: The return value should be a valid `XcodebuildOption`
        AND: The option name must match the `xcodebuild_option` decorator name value
        """
        params_sig = inspect.signature(attr).parameters

        value_param_sig = params_sig.get("value", None)

        if value_param_sig is None:
            option = attr()
            assert isinstance(option, XcodebuildOption)
        elif value_param_sig.annotation == str:
            option = attr("Some String")
            assert isinstance(option, XcodebuildOptionWithValue)
        elif value_param_sig.annotation == Destination:
            option = attr(Destination(platform="iOS"))
            assert isinstance(option, XcodebuildOptionWithValue)
        else:
            pytest.fail(f"Unexpected value type {value_param_sig.annotation}")

        assert option.name == attr.__xcodebuild_option__


class TestXcodebuildCommand:
    def test_invalid_xcodebuild_option(self):
        """
        GIVEN: A `XcodebuildCommand` with an invalid `XcodebuildOption`

        WHEN: parsing the command

        THEN: A `CommandError` should be raised
        """
        invalid_option = XcodebuildOption("-invalid")
        command = XcodebuildCommand(action="build", options=[invalid_option])

        with pytest.raises(CommandError):
            command.parse()

    def test_invalid_action(self):
        """
        GIVEN: A `XcodebuildCommand` with an invalid action

        WHEN: parsing the command

        THEN: A `CommandError` should be raised
        """
        command = XcodebuildCommand(action="invalid")

        with pytest.raises(CommandError):
            command.parse()

    def test_parsing_works_correctly(self):
        """
        GIVEN: A `XcodebuildCommand` with a valid action and options

        WHEN: parsing the command

        THEN: The returned list of str should be correct
        """
        expected_parsed_command = [
            "xcodebuild",
            "build",
            "-quiet",
            "-project",
            "/tmp/project",
        ]

        command = XcodebuildCommand(
            action="build",
            options=[
                XcodebuildOptions.quiet(),
                XcodebuildOptions.project("/tmp/project"),
            ],
        )

        parsed_command = command.parse()

        assert expected_parsed_command == parsed_command


class TestXcodebuildTestCommand:
    def test_parse_returns_correct_command(self, fake_udid):
        """
        GIVEN: A `XcodebuildTestCommand` with correct arguments

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        """
        expected_command = [
            "xcodebuild",
            "test-without-building",
            "-xctestrun",
            "/tmp/project",
            "-destination",
            f"platform=iOS,id={fake_udid}",
            "-only-test-configuration",
            "Some Configuration",
            "-only-testing",
            "test1",
            "-skip-testing",
            "test2",
        ]

        command = XcodebuildTestCommand(
            xctestrun="/tmp/project",
            destination=IOSDestination(id=fake_udid),
            only_testing=["test1"],
            skip_testing=["test2"],
            test_configuration="Some Configuration",
        )

        parsed_command = command.parse()

        assert expected_command == parsed_command

    def test_parse_multiple_only_testing(self, fake_udid):
        """
        GIVEN: A `XcodebuildTestCommand` with multiple only_testing

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        AND: Specifically contain multiple `-only-testing` and `-skip-testing` options
        """
        expected_command = [
            "xcodebuild",
            "test-without-building",
            "-xctestrun",
            "/tmp/project",
            "-destination",
            f"platform=iOS,id={fake_udid}",
            "-only-test-configuration",
            "Some Configuration",
            "-only-testing",
            "test1",
            "-only-testing",
            "test2",
            "-skip-testing",
            "test3",
            "-skip-testing",
            "test4",
        ]

        command = XcodebuildTestCommand(
            xctestrun="/tmp/project",
            destination=IOSDestination(id=fake_udid),
            only_testing=["test1", "test2"],
            skip_testing=["test3", "test4"],
            test_configuration="Some Configuration",
        )

        parsed_command = command.parse()

        assert expected_command == parsed_command

    def test_parse_result_bundle_path(self, fake_udid):
        """
        GIVEN: A `XcodebuildTestCommand` with a result_bundle_path

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        """

        expected_command = [
            "xcodebuild",
            "test-without-building",
            "-xctestrun",
            "/tmp/project",
            "-destination",
            f"platform=iOS,id={fake_udid}",
            "-only-test-configuration",
            "Some Configuration",
            "-resultBundlePath",
            "/tmp/result_bundle",
        ]

        command = XcodebuildTestCommand(
            xctestrun="/tmp/project",
            destination=IOSDestination(id=fake_udid),
            result_bundle_path="/tmp/result_bundle",
            test_configuration="Some Configuration",
        )

        assert expected_command == command.parse()


class TestXcodebuildTestEnumerationCommand:
    def test_parse_returns_correct_command(self, fake_udid):
        """
        GIVEN: A `XcodebuildTestEnumerationCommand` with correct arguments

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        """
        expected_command = [
            "xcodebuild",
            "test-without-building",
            "-xctestrun",
            "/tmp/project",
            "-destination",
            f"platform=iOS,id={fake_udid}",
            "-destination-timeout",
            "1",
            "-enumerate-tests",
            "-test-enumeration-style",
            "flat",
            "-test-enumeration-format",
            "json",
            "-test-enumeration-output-path",
            "/tmp/test_enumeration.json",
        ]

        command = XcodebuildTestEnumerationCommand(
            xctestrun="/tmp/project",
            destination=IOSDestination(id=fake_udid),
            enumeration_style="flat",
            enumeration_format="json",
            output_path="/tmp/test_enumeration.json",
        )

        parsed_command = command.parse()

        assert expected_command == parsed_command


class TestXcodebuildBuildCommand:
    @pytest.mark.parametrize("action", ["build", "build-for-testing"])
    @pytest.mark.parametrize(
        "workspace,project",
        [
            ["/tmp/workspace", None],
            [None, "/tmp/project"],
        ],
    )
    def test_parse_returns_correct_command(self, action, workspace, project, fake_udid):
        """
        GIVEN: A `XcodebuildBuildCommand` with correct arguments

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        """
        expected_command = [
            "xcodebuild",
            action,
            "-workspace" if workspace else "-project",
            workspace if workspace else project,
            "-scheme",
            "Some Scheme",
            "-configuration",
            "Some Configuration",
            "-destination",
            f"platform=iOS,id={fake_udid}",
            "-destination-timeout",
            "1",
            "-derivedDataPath",
            "/tmp/derived_data",
            "-IDECustomBuildProductsPath",
            "",
            "-IDECustomBuildIntermediatesPath",
            "",
        ]

        command = XcodebuildBuildCommand(
            action=action,
            workspace=workspace,
            project=project,
            scheme="Some Scheme",
            configuration="Some Configuration",
            destination=IOSDestination(id=fake_udid),
            derived_data_path="/tmp/derived_data",
        )

        parsed_command = command.parse()

        assert expected_command == parsed_command

    def test_init_without_workspace_and_project_should_raise(self):
        """
        GIVEN: A `XcodebuildBuildCommand` without workspace and project

        WHEN: initializing the command

        THEN: A `CommandError` should be raised
        """
        with pytest.raises(CommandError):
            XcodebuildBuildCommand(
                action="build",
                destination=MagicMock(spec=IOSDestination),
                configuration=MagicMock(spec=str),
                derived_data_path=MagicMock(spec=str),
                scheme=MagicMock(spec=str),
            )

    @pytest.mark.parametrize("action", ["build", "build-for-testing"])
    def test_init_when_workspace_and_project_should_raise(self, action):
        """
        GIVEN: A `XcodebuildBuildCommand` with both workspace and project

        WHEN: initializing the command

        THEN: A `CommandError` should be raised
        """
        with pytest.raises(CommandError):
            XcodebuildBuildCommand(
                action=action,
                workspace="/tmp/workspace",
                project="/tmp/project",
                destination=MagicMock(spec=IOSDestination),
                configuration=MagicMock(spec=str),
                derived_data_path=MagicMock(spec=str),
                scheme=MagicMock(spec=str),
            )


class TestXcodebuildListCommand:
    @pytest.mark.parametrize(
        "workspace,project",
        [
            ["/tmp/workspace", None],
            [None, "/tmp/project"],
        ],
    )
    def test_parse_returns_correct_command(self, workspace, project, fake_udid):
        """
        GIVEN: A `XcodebuildListCommand` with correct arguments

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        """
        expected_command = [
            "xcodebuild",
            "-list",
            "-workspace" if workspace else "-project",
            workspace if workspace else project,
            "-json",
        ]

        command = XcodebuildListCommand(
            workspace=workspace,
            project=project,
        )

        parsed_command = command.parse()

        assert expected_command == parsed_command


class TestXcodebuildShowTestPlansCommand:
    @pytest.mark.parametrize(
        "workspace,project",
        [
            ["/tmp/workspace", None],
            [None, "/tmp/project"],
        ],
    )
    def test_parse_returns_correct_command(self, workspace, project, fake_udid):
        """
        GIVEN: A `XcodebuildShowTestPlansCommand` with correct arguments

        WHEN: parsing the command

        THEN: The returned list of str should represent the correct command
        """
        expected_command = [
            "xcodebuild",
            "-showTestPlans",
            "-workspace" if workspace else "-project",
            workspace if workspace else project,
            "-json",
        ]

        command = XcodebuildShowTestPlansCommand(
            workspace=workspace,
            project=project,
        )

        parsed_command = command.parse()

        assert expected_command == parsed_command

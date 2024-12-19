import inspect

import pytest

from core.subprocesses.process import CommandError
from core.subprocesses.xcodebuild_command import XcodeBuildOptions, XcodeBuildOption, XcodeBuildOptionWithValue, \
    XcodeBuildCommand


def xcode_build_options_attributes():
    attributes = []

    for attr_name in dir(XcodeBuildOptions):
        if attr_name.startswith("__"):
            # Ignore pythons private attributes
            continue
        if attr_name.startswith("_XcodeBuildOptions__"):
            # Ignore user defined private attributes
            continue
        attr = getattr(XcodeBuildOptions, attr_name)
        attributes.append(attr)

    return attributes


@pytest.mark.parametrize("attr", xcode_build_options_attributes())
class TestXcodebuildOptions:
    def test_all_methods_are_xcode_option_decorated(self, attr):
        """
        GIVEN: A `XcodeBuildOptions` attribute

        THEN: The attribute must be a callable
        AND: Must be decorated with `@xcode_option`.
        """
        assert callable(attr)
        assert hasattr(attr, '__xcode_build_option__')

    def test_all_methods_signature(self, attr):
        """
        GIVEN: A `XcodeBuildOptions` attribute

        WHEN: checking getting the signature on that attribute

        THEN: The only param name must be "value"
        OR: There should be no param
        """
        params_sig = inspect.signature(attr).parameters

        for param_name in params_sig.keys():
            assert param_name == "value"

    def test_returned_value_is_correct_xcode_option(self, attr):
        """
        GIVEN: A `XcodeBuildOptions` attribute

        WHEN: Calling the attribute

        THEN: The return value should be a valid `XcodeBuildOption`
        AND: The option name must match the `xcode_option` decorator name value
        """
        params_sig = inspect.signature(attr).parameters

        value_param_sig = params_sig.get("value", None)

        if value_param_sig is None:
            option = attr()
            assert isinstance(option, XcodeBuildOption)
        elif value_param_sig.annotation == str:
            option = attr("Some String")
            assert isinstance(option, XcodeBuildOptionWithValue)
        elif value_param_sig.annotation == dict:
            option = attr({"Key": "Value"})
            assert isinstance(option, XcodeBuildOptionWithValue)
        else:
            pytest.fail("Unexpected value type")

        assert option.name == attr.__xcode_build_option__


class TestXcodeBuildCommand:
    def test_invalid_xcode_build_option(self):
        """
        GIVEN: A `XcodeBuildCommand` with an invalid `XcodeBuildOption`

        WHEN: parsing the command

        THEN: A `CommandError` should be raised
        """
        invalid_option = XcodeBuildOption("-invalid")
        command = XcodeBuildCommand(action="build", options=[invalid_option])

        with pytest.raises(CommandError):
            command.parse()

    def test_invalid_action(self):
        """
        GIVEN: A `XcodeBuildCommand` with an invalid action

        WHEN: parsing the command

        THEN: A `CommandError` should be raised
        """
        command = XcodeBuildCommand(action="invalid")

        with pytest.raises(CommandError):
            command.parse()

    def test_parsing_works_correctly(self):
        """
        GIVEN: A `XcodeBuildCommand` with a valid action and options

        WHEN: parsing the command

        THEN: The returned list of str should be correct
        """
        expected_parsed_command = ["xcodebuild", "build", "-quiet", "-project", "/tmp/project"]

        command = XcodeBuildCommand(action="build",
                                    options=[XcodeBuildOptions.quiet(), XcodeBuildOptions.project("/tmp/project")])

        parsed_command = command.parse()

        assert expected_parsed_command == parsed_command

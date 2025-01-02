import functools
from typing import Literal, get_args, Optional, Self

from pydantic import BaseModel, model_validator, Field

from core.subprocesses.process import ProcessCommand, CommandError


class XcodebuildOption:
    """
    A xcodebuild build option that does not require a value
    """

    def __init__(self, name: str):
        self.name = name


class XcodebuildOptionWithValue(XcodebuildOption):
    """
    A xcodebuild option that requires a value
    """

    def __init__(self, name: str, value: str):
        super().__init__(name)
        if not isinstance(value, str):
            raise ValueError("Value must be either True or of type str")
        self.value = value


def xcodebuild_option(option_name: str):
    """
    Decorator to register a function as providing a valid XcodebuildOption.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__xcodebuild_option__ = option_name
        return wrapper

    return decorator


class Destination(BaseModel):
    platform: str


class IOSDestination(Destination):
    platform: Literal["iOS"] = "iOS"
    id: Optional[str] = None
    name: Optional[str] = None

    @model_validator(mode="after")
    def verify_id_or_name(self) -> Self:
        if (self.id and self.name) or (not self.id and not self.name):
            raise ValueError("Expected id or name, but not both.")
        return self


class XcodebuildOptions:
    """
    Contains all supported `xcodebuild` options as static methods.

    The returned option by each of the methods can be passed to the `XcodebuildCommand`

    To understand each of the options please check the `xcodebuild` man page.
    """

    @staticmethod
    def __get_option_name(method: callable):
        return getattr(method, "__xcodebuild_option__")

    # TODO: Maybe we need -enumerate-tests to get all tests
    @staticmethod
    @xcodebuild_option("-quiet")
    def quiet():
        return XcodebuildOption(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.quiet)
        )

    @staticmethod
    @xcodebuild_option("-project")
    def project(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.project), value
        )

    @staticmethod
    @xcodebuild_option("-workspace")
    def workspace(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.workspace), value
        )

    @staticmethod
    @xcodebuild_option("-scheme")
    def scheme(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.scheme), value
        )

    @staticmethod
    @xcodebuild_option("-target")
    def target(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.target), value
        )

    @staticmethod
    @xcodebuild_option("-destination")
    def destination(value: Destination):
        destination_key_value_pairs = [
            f"{key}={value}"
            for key, value in value.model_dump(exclude_none=True).items()
        ]
        destination_as_string = ",".join(destination_key_value_pairs)
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.destination),
            destination_as_string,
        )

    @staticmethod
    @xcodebuild_option("-destination-timeout")
    def destination_timeout(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.destination_timeout),
            value,
        )

    @staticmethod
    @xcodebuild_option("-derivedDataPath")
    def derived_data_path(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.derived_data_path),
            value,
        )

    @staticmethod
    @xcodebuild_option("-resultBundlePath")
    def result_bundle_path(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.result_bundle_path),
            value,
        )

    @staticmethod
    @xcodebuild_option("-list")
    def list():
        return XcodebuildOption(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.list)
        )

    @staticmethod
    @xcodebuild_option("-xctestrun")
    def xctestrun(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.xctestrun), value
        )

    @staticmethod
    @xcodebuild_option("-skip-testing")
    def skip_testing(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.skip_testing), value
        )

    @staticmethod
    @xcodebuild_option("-only-testing")
    def only_testing(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.only_testing), value
        )

    @staticmethod
    @xcodebuild_option("-enumerate-tests")
    def enumerate_tests():
        return XcodebuildOption(
            XcodebuildOptions.__get_option_name(XcodebuildOptions.enumerate_tests),
        )

    @staticmethod
    @xcodebuild_option("-test-enumeration-style")
    def test_enumeration_style(value: str):
        """
        :param value: "hierarchical", "flat"
        """
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(
                XcodebuildOptions.test_enumeration_style
            ),
            value,
        )

    @staticmethod
    @xcodebuild_option("-test-enumeration-format")
    def test_enumeration_format(value: str):
        """
        :param value: "text", "json"
        """
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(
                XcodebuildOptions.test_enumeration_format
            ),
            value,
        )

    @staticmethod
    @xcodebuild_option("-test-enumeration-output-path")
    def test_enumeration_output_path(value: str):
        return XcodebuildOptionWithValue(
            XcodebuildOptions.__get_option_name(
                XcodebuildOptions.test_enumeration_output_path
            ),
            value,
        )


def _valid_option_names():
    option_names = []

    for attr_name in dir(XcodebuildOptions):
        if attr_name.startswith("__"):
            # Ignore pythons private attributes
            continue
        if attr_name.startswith("_XcodebuildOptions__"):
            # Ignore user defined private attributes
            continue

        attr = getattr(XcodebuildOptions, attr_name)
        if not callable(attr):
            continue

        xcodebuild_option_name = getattr(attr, "__xcodebuild_option__", None)
        if xcodebuild_option_name is None:
            continue

        option_names.append(xcodebuild_option_name)

    return option_names


class XcodebuildCommand(ProcessCommand):
    """
    A command parser for `xcodebuild`
    """

    ACTION_TYPE = Literal[
        "build", "build-for-testing", "clean", "test-without-building", None
    ]

    def __init__(
        self,
        action: ACTION_TYPE,
        options: Optional[list[XcodebuildOption]] = None,
    ):
        """
        :param action: The main action to execute. Can be `None` as not every command requires an action.
        :param options: Additional options to pass to `xcodebuild`. Refer to `XcodebuildOptions` for valid options.
        """
        self.action = action
        self.options = options

    @property
    def valid_actions(self):
        return get_args(self.ACTION_TYPE)

    def parse(self) -> [str]:
        command = ["xcodebuild"]

        if self.action not in self.valid_actions:
            raise CommandError(
                f"Invalid action: {self.action}, must be one of {self.valid_actions}"
            )

        if self.action is not None:
            command.append(self.action)

        valid_option_names = _valid_option_names()

        for option in self.options:
            if option.name not in valid_option_names:
                raise CommandError(
                    f"Invalid option name: {option.name}, must be one of {valid_option_names}"
                )

            if isinstance(option, XcodebuildOptionWithValue):
                command.extend([option.name, option.value])
            elif isinstance(option, XcodebuildOption):
                command.append(option.name)
            else:
                raise CommandError(f"Unknown option type: {type(option).__name__}")
        return command


class XcodebuildTestCommand(XcodebuildCommand):
    """
    A convenience command parser for the `xcodebuild test-without-building` command.
    """

    def __init__(
        self,
        xctestrun: str,
        scheme: str,
        destination: IOSDestination,
        only_testing: Optional[str] = None,
        skip_testing: Optional[str] = None,
    ):
        """
        :param xctestrun: Path to the xctestrun bundle.
        :param scheme: The scheme the xctestrun was built with.
        :param destination: On which device to run the test.
        :param only_testing: Test identifier of the only test that should be executed.
        :param skip_testing: Test identifier of the test that should be skipped.
        """
        options = [
            XcodebuildOptions.xctestrun(xctestrun),
            XcodebuildOptions.scheme(scheme),
            XcodebuildOptions.destination(destination),
        ]
        if only_testing:
            options.append(XcodebuildOptions.only_testing(only_testing))
        if skip_testing:
            options.append(XcodebuildOptions.skip_testing(skip_testing))

        super().__init__(action="test-without-building", options=options)


class XcodebuildTestEnumerationCommand(XcodebuildCommand):
    """
    A convenience command parser for enumerating over tests using the `xcodebuild test-without-building` as a base.
    """

    def __init__(
        self,
        xctestrun: str,
        destination: IOSDestination,
        enumeration_style: Literal["hierarchical", "flat"] = "flat",
        enumeration_format: Literal["text", "json"] = "json",
        output_path: Optional[str] = None,
    ):
        options = [
            XcodebuildOptions.xctestrun(xctestrun),
            XcodebuildOptions.destination(destination),
            XcodebuildOptions.enumerate_tests(),
            XcodebuildOptions.test_enumeration_style(enumeration_style),
            XcodebuildOptions.test_enumeration_format(enumeration_format),
        ]

        if output_path is not None:
            options.append(XcodebuildOptions.test_enumeration_output_path(output_path))

        super().__init__(action="test-without-building", options=options)

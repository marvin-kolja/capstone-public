import functools
from typing import Literal, get_args, Optional

from core.subprocesses.process import ProcessCommand


class XcodeBuildOption:
    """
    A xcodebuild build option that does not require a value
    """
    def __init__(self, name: str):
        self.name = name


class XcodeBuildOptionWithValue(XcodeBuildOption):
    """
    A xcodebuild option that requires a value
    """
    def __init__(self, name: str, value: str):
        super().__init__(name)
        if not isinstance(value, str):
            raise ValueError("Value must be either True or of type str")
        self.value = value


def xcode_option(option_name: str):
    """
    Decorator to register a function as providing a valid XcodeBuildOption.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__xcode_build_option__ = option_name
        return wrapper

    return decorator


class XcodeBuildOptions:
    """
    Contains all supported `xcodebuild` options as static methods.

    The returned option by each of the methods can be passed to the `XcodeBuildCommand`

    To understand each of the options please check the `xcodebuild` man page.
    """

    @staticmethod
    def __get_option_name(method: callable):
        return getattr(method, "__xcode_build_option__")

    # TODO: Maybe we need -enumerate-tests to get all tests
    @staticmethod
    @xcode_option("-quiet")
    def quiet():
        return XcodeBuildOption(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.quiet))

    @staticmethod
    @xcode_option("-project")
    def project(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.project), value)

    @staticmethod
    @xcode_option("-workspace")
    def workspace(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.workspace), value)

    @staticmethod
    @xcode_option("-scheme")
    def scheme(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.scheme), value)

    @staticmethod
    @xcode_option("-target")
    def target(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.target), value)

    @staticmethod
    @xcode_option("-destination")
    def destination(value: dict):
        destination_key_value_pairs = [f"{key}={value}" for key, value in value.items()]
        destination_as_string = ",".join(destination_key_value_pairs)
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.destination),
                                         destination_as_string)

    @staticmethod
    @xcode_option("-destination-timeout")
    def destination_timeout(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.destination_timeout),
                                         value)

    @staticmethod
    @xcode_option("-derivedDataPath")
    def derived_data_path(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.derived_data_path),
                                         value)

    @staticmethod
    @xcode_option("-resultBundlePath")
    def result_bundle_path(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.result_bundle_path),
                                         value)

    @staticmethod
    @xcode_option("-list")
    def list():
        return XcodeBuildOption(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.list))

    @staticmethod
    @xcode_option("-xctestrun")
    def xctestrun(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.xctestrun), value)

    @staticmethod
    @xcode_option("-skip-testing")
    def skip_testing(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.skip_testing), value)

    @staticmethod
    @xcode_option("-only-testing")
    def only_testing(value: str):
        return XcodeBuildOptionWithValue(XcodeBuildOptions.__get_option_name(XcodeBuildOptions.only_testing), value)


class XcodeBuildCommand(ProcessCommand):
    """
    A command parser for `xcodebuild`
    """

    ACTION_TYPE = Literal["build", "build-for-testing", "clean", "test-without-building", None]

    def __init__(
            self,
            action: ACTION_TYPE,
            options: Optional[list[XcodeBuildOption]] = None,
    ):
        """
        :param action: The main action to execute. Can be `None` as not every command requires an action.
        :param options: Additional options to pass to `xcodebuild`. Refer to `XcodeBuildOptions` for valid options.
        """
        self.action = action
        self.options = options

    @property
    def valid_actions(self):
        return get_args(self.ACTION_TYPE)

    def parse(self) -> [str]:
        raise NotImplementedError

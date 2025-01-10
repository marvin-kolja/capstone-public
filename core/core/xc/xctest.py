import contextlib
import logging
import pathlib
import tempfile
from typing import Any, Generator, Optional

from pydantic import BaseModel, field_validator

from core.common.plist_reader import read_plist
from core.exceptions.common import InvalidFileContent
from core.exceptions.xctest import ListEnumerationFailure
from core.subprocesses.process import async_run_process, ProcessException
from core.subprocesses.xcodebuild_command import (
    IOSDestination,
    XcodebuildTestEnumerationCommand,
    XcodebuildTestCommand,
)
from core.xc.xctestrun import Xctestrun

logger = logging.getLogger(__name__)


class XctestOverview(BaseModel):
    """
    Values from test enumeration result

    :param testPlan: The name of the test plan.
    :param disabledTests: The list of identifiers of disabled tests.
    :param enabledTests: The list of identifiers of enabled tests.
    """

    testPlan: str
    disabledTests: list[str]
    enabledTests: list[str]

    @field_validator("disabledTests", "enabledTests", mode="before")
    def extract_test_ids(cls, data: Any) -> Any:
        if isinstance(data, list):
            return [test["identifier"] for test in data]
        return data


class XcTestEnumerationResult(BaseModel):
    """
    Test enumeration result
    """

    errors: list[str]
    values: list[XctestOverview]


class Xctest:
    """
    This class is responsible for interactions with xcode testing, such as listing and running tests.
    """

    @staticmethod
    @contextlib.contextmanager
    def _temporary_file_path(file_name: str) -> Generator[pathlib.Path, Any, None]:
        """
        Creates a temporary directory and returns a path to a non-existent file in that directory.

        :param file_name: The name of the file to use for the temporary file path.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger.debug(f"Temporary directory created: {tmp_dir}")
            yield pathlib.Path(tmp_dir, file_name)
        logger.debug(f"Temporary directory deleted: {tmp_dir}")

    @staticmethod
    def _read_file(file_path: str) -> str:
        """
        Reads the content of the file.

        :param file_path: The path to the file to read.

        :return: The content of the file as a string.

        :raises InvalidFileContent: when unable to read the file.
        :raises FileNotFoundError: when the file does not exist.
        """
        with open(file_path, "r") as f:
            try:
                return f.read()
            except Exception as e:
                logger.error(f"Failed to read the file: {e}")
                raise InvalidFileContent from e

    @staticmethod
    def _parse_test_enumeration_result(file_content: str) -> XcTestEnumerationResult:
        """
        Parses the test enumeration result from a string.

        :param file_content: The content of the file to parse.

        :return: The parsed test enumeration result.

        :raises InvalidFileContent: when unable to validate the content.
        """
        try:
            return XcTestEnumerationResult.model_validate_json(file_content)
        except Exception as e:
            logger.error(f"Failed to validate the result of the test enumeration: {e}")
            raise InvalidFileContent from e

    @staticmethod
    async def list_tests(
        xctestrun_path: str,
        destination: IOSDestination,
    ) -> XctestOverview:
        """
        Gets the list of tests using the xctestrun file. The xctestrun file contains the testing bundle path and testing
        host path. These are then installed on the target device, and it is checked which tests the testing bundle
        contains.

        This uses the :class:`core.subprocesses.XcodebuildTestEnumerationCommand` command to enumerate the tests.

        *Note: This does not check if the destination is ready. If it's a physical device you may want to prepare it
        before calling this method.*

        :param xctestrun_path: The path to the xctestrun file
        :param destination: The destination the test bundle and app is installed on.
        :return: The test enumeration result in format of the :class:`.Xctests` model`

        :raises ProcessException: when the executed command fails.
        :raises ListTestsFailure: when the command succeeds, but the result contains errors.
        """
        logger.debug(f"Getting list of tests for {xctestrun_path}")
        with Xctest._temporary_file_path("test_enumeration.json") as tmp_file:
            logger.debug(f"Starting test enumeration with output file: {tmp_file}")

            command = XcodebuildTestEnumerationCommand(
                xctestrun=xctestrun_path,
                destination=destination,
                enumeration_style="flat",
                enumeration_format="json",
                output_path=tmp_file.absolute().as_posix(),
            )

            try:
                stdout, stderr = await async_run_process(command=command)
            except ProcessException as e:
                logger.error(
                    f"Failed to get list of tests due to xcodebuild command failed: {e}"
                )
                raise

            logger.debug(
                f"Trying to read the result of the test enumeration from file {tmp_file}"
            )

            file_content = Xctest._read_file(tmp_file)
            result = Xctest._parse_test_enumeration_result(file_content)

            if result.errors:
                logger.error("Process finished, but there are errors in the result")
                raise ListEnumerationFailure(
                    stderr=stderr,
                    stdout=stdout,
                    errors=result.errors,
                )

            if len(result.values) != 1:
                logger.error(
                    f"Expected exactly one value in the results, but got {len(result.values)}"
                )
                raise InvalidFileContent("Expected exactly one value in the result")

            return result.values[0]

    @staticmethod
    async def run_test(
        xctestrun_path: str,
        destination: IOSDestination,
        test_configuration: str,
        only_testing: Optional[list[str]] = None,
        skip_testing: Optional[list[str]] = None,
        xcresult_path: Optional[str] = None,
    ) -> None:
        """
        Starts executing the tests using the xctestrun file. The xctestrun file contains the testing bundle path and
        testing host path. These are then installed on the target device, and the tests are executed. This happens by
        using the :class:`core.subprocesses.XcodebuildTestCommand` command.

        *Note: This does not check if the destination is ready. If it's a physical device you may want to prepare it
        before calling this method.*

        :param xctestrun_path: The path to the xctestrun file
        :param destination: The destination the test bundle and app is installed on.
        :param test_configuration: The test configuration to use. While Xcode supports executing tests using multiple
        we support only one and rather allow the user to specify the test configuration in the test plan.
        :param only_testing: The identifiers of the tests to run. If empty all tests are run.
        :param skip_testing: The identifiers of the tests to skip. If empty no tests are skipped.
        :param xcresult_path: The path to save the result bundle to. If not provided xcodebuild will decide where to
        save it.

        :raises ProcessException: when the executed command fails.
        """
        logger.debug(f"Start execution of tests for {xctestrun_path}")

        command = XcodebuildTestCommand(
            xctestrun=xctestrun_path,
            destination=destination,
            only_testing=only_testing,
            skip_testing=skip_testing,
            test_configuration=test_configuration,
            result_bundle_path=xcresult_path,
        )

        try:
            await async_run_process(command=command)
        except ProcessException as e:
            logger.error(
                f"Failed to run the test for {xctestrun_path} due to process failure with return code: {e.return_code}"
            )
            raise

        logger.debug(f"Finished running tests for {xctestrun_path}")

    @staticmethod
    def parse_xctestrun(path: str) -> Xctestrun:
        """
        Extracts important information such as the test plan name, test configurations, and test targets from the
        `.xctestrun` file.

        It also replaces ``__TESTROOT__`` with the actual parent directory of the xctestrun file. This way the
        ``TestHostPath`` and ``UITargetAppPath`` fields have the correct full paths.

        :param path: The path to the xctestrun file.
        """
        plist_data = read_plist(path)

        for test_configuration in plist_data["TestConfigurations"]:
            for test_target in test_configuration["TestTargets"]:
                keys = ["TestHostPath", "UITargetAppPath"]

                for key in keys:
                    value = test_target.get(key)
                    if value:
                        test_target[key] = value.replace(
                            "__TESTROOT__",
                            pathlib.Path(path).absolute().parent.as_posix(),
                        )

        return Xctestrun.model_validate(plist_data)

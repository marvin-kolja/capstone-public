import contextlib
import logging
import pathlib
import tempfile
from typing import Any, Generator

from pydantic import BaseModel, Field

from core.exceptions.common import InvalidFileContent
from core.exceptions.xcodebuild import XcodebuildException
from core.exceptions.xctestrun import ListEnumerationFailure
from core.subprocesses.process import Process
from core.subprocesses.xcodebuild_command import (
    IOSDestination,
    XcodebuildTestEnumerationCommand,
)

logger = logging.getLogger(__name__)


class Xctest(BaseModel):
    """
    Single xcode test
    """

    identifier: str


class Xctests(BaseModel):
    """
    Values from test enumeration result
    """

    testPlan: str
    disabledTests: list[Xctest]
    enabledTests: list[Xctest]


class TestEnumerationResult(BaseModel):
    """
    Test enumeration result
    """

    errors: list[str]
    values: list[Xctests]


class Xctestrun:
    """
    Interactions with the xctestrun file such as listing the tests or executing them.
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

        :raises: `InvalidFileContent` when unable to read the file.
        :raises: `FileNotFoundError` when the file does not exist.
        """
        with open(file_path, "r") as f:
            try:
                return f.read()
            except Exception as e:
                logger.error(f"Failed to read the file: {e}")
                raise InvalidFileContent from e

    @staticmethod
    def _parse_test_enumeration_result(file_content: str) -> TestEnumerationResult:
        """
        Parses the test enumeration result from a string.

        :param file_content: The content of the file to parse.

        :return: The parsed test enumeration result.

        :raises: `InvalidFileContent` when unable to validate the content.
        """
        try:
            return TestEnumerationResult.model_validate_json(file_content)
        except Exception as e:
            logger.error(f"Failed to validate the result of the test enumeration: {e}")
            raise InvalidFileContent from e

    @staticmethod
    async def list_tests(xctestrun_path: str, destination: IOSDestination) -> Xctests:
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

        :raises: `XcodebuildException` when the executed command fails.
        :raises: `ListTestsFailure` when the command succeeds, but the result contains errors.
        """
        logger.debug(f"Getting list of tests for {xctestrun_path}")
        with Xctestrun._temporary_file_path("test_enumeration.json") as tmp_file:
            logger.debug(f"Starting test enumeration with output file: {tmp_file}")

            command = XcodebuildTestEnumerationCommand(
                xctestrun=xctestrun_path,
                destination=destination,
                enumeration_style="flat",
                enumeration_format="json",
                output_path=tmp_file.absolute().as_posix(),
            )

            process = Process(command=command)
            await process.execute()
            stdout, stderr = await process.wait()

            if process.failed:
                logger.error(
                    f"Failed to get list of tests due to process failed with return code: {process.returncode}"
                )
                raise XcodebuildException(
                    stdout=stdout,
                    stderr=stderr,
                    return_code=process.returncode,
                )

            logger.debug(
                f"Trying to read the result of the test enumeration from file {tmp_file}"
            )

            file_content = Xctestrun._read_file(tmp_file)
            result = Xctestrun._parse_test_enumeration_result(file_content)

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

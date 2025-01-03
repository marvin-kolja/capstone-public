import json
import pathlib
from unittest.mock import patch, MagicMock

import pytest

from core.exceptions.common import InvalidFileContent
from core.exceptions.xctest import ListEnumerationFailure
from core.subprocesses.process import ProcessException
from core.subprocesses.xcodebuild_command import (
    XcodebuildTestEnumerationCommand,
    IOSDestination,
    XcodebuildTestCommand,
)
from core.test_session.xctest import Xctest, XctestOverview


@pytest.fixture
def fake_tmp_file():
    return pathlib.Path("/tmp/file")


@pytest.fixture
def mock_xcodebuild_run():
    with patch(
        "core.test_session.xctest.async_run_process", return_value=([], [])
    ) as run_mock:
        yield run_mock


@pytest.fixture
def success_test_enumeration_result():
    return {
        "errors": [],
        "values": [
            {
                "testPlan": "plan",
                "disabledTests": [],
                "enabledTests": [
                    {
                        "identifier": "identifier",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def mock_read_file(success_test_enumeration_result):
    with patch("core.test_session.xctest.Xctest._read_file") as mock:
        mock.return_value = json.dumps(success_test_enumeration_result)
        yield mock


@pytest.fixture
def mock_temporary_file_path(fake_tmp_file):
    with patch("core.test_session.xctest.Xctest._temporary_file_path") as mock_context:
        mock_enter = MagicMock(return_value=fake_tmp_file)
        mock_context.return_value.__enter__ = mock_enter
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        yield mock_enter


class TestXctestListTests:
    """
    Test Xctest.list_tests method
    """

    @pytest.mark.asyncio
    async def test_list_tests_calls_enumeration_command(
        self,
        mock_read_file,
        mock_temporary_file_path,
        mock_xcodebuild_run,
        success_test_enumeration_result,
        fake_udid,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `list_tests`

        THEN: A `XcodebuildTestEnumerationCommand` should be created using the correct values.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        with patch.object(
            XcodebuildTestEnumerationCommand, "__init__", return_value=None
        ) as mock_init:
            await Xctest.list_tests(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
            )

            mock_init.assert_called_once_with(
                destination=IOSDestination(id=fake_udid),
                enumeration_format="json",
                enumeration_style="flat",
                output_path=mock_temporary_file_path().absolute().as_posix(),
                xctestrun=fake_xctestrun,
            )

    @pytest.mark.asyncio
    async def test_list_tests_returns_result(
        self,
        mock_read_file,
        mock_temporary_file_path,
        mock_xcodebuild_run,
        success_test_enumeration_result,
        fake_udid,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `list_tests`

        THEN: The result returned should be the same as the test enumeration result.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        result = await Xctest.list_tests(
            xctestrun_path=fake_xctestrun,
            destination=IOSDestination(
                id=fake_udid,
            ),
        )

        assert result == XctestOverview.model_validate(
            success_test_enumeration_result.get("values")[0]
        )

    @pytest.mark.asyncio
    async def test_list_tests_xcodebuild_exception(
        self,
        mock_read_file,
        mock_temporary_file_path,
        mock_xcodebuild_run,
        success_test_enumeration_result,
        fake_udid,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `list_tests`
        AND: The xcodebuild run fails and raises a `ProcessException`

        THEN: A `ProcessException` should be raised.
        AND: The exception should contain the stdout, stderr and return code of the process.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"
        mock_xcodebuild_run.side_effect = ProcessException(
            stdout=["stdout"], stderr=["stderr"], return_code=1
        )

        with pytest.raises(ProcessException) as e:
            await Xctest.list_tests(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
            )

        assert e.value.stdout == ["stdout"]
        assert e.value.stderr == ["stderr"]
        assert e.value.return_code == 1

    @pytest.mark.asyncio
    async def test_list_tests_list_enumeration_failure(
        self,
        mock_read_file,
        mock_temporary_file_path,
        mock_xcodebuild_run,
        success_test_enumeration_result,
        fake_udid,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `list_tests`
        AND: The xcodebuild run succeeds
        AND: The result contains errors

        THEN: A `ListEnumerationFailure` should be raised.
        AND: The exception should contain the stdout and stderr of the process and the errors of the result.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"
        mock_read_file.return_value = json.dumps(
            {
                "errors": ["error"],
                "values": [],
            }
        )

        with pytest.raises(ListEnumerationFailure) as e:
            await Xctest.list_tests(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
            )

        assert e.value.stdout == []
        assert e.value.stderr == []
        assert e.value.errors == ["error"]

    @pytest.mark.asyncio
    async def test_list_tests_invalid_file_content(
        self,
        mock_read_file,
        mock_temporary_file_path,
        mock_xcodebuild_run,
        success_test_enumeration_result,
        fake_udid,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `list_tests`
        AND: The xcodebuild run succeeds
        AND: The result contains no errors
        AND: The result contains more than one value

        THEN: An `InvalidFileContent` should be raised.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"
        mock_read_file.return_value = "Invalid content"

        with pytest.raises(InvalidFileContent):
            await Xctest.list_tests(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
            )


class TestXctestRunTest:
    """
    Test Xctest.run_test method
    """

    @pytest.mark.parametrize(
        "only_testing, skip_testing",
        [
            (None, None),
            (
                ["test1"],
                ["test2"],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_run_test_calls_test_command(
        self,
        mock_xcodebuild_run,
        fake_udid,
        only_testing,
        skip_testing,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `run_test`

        THEN: A `XcodebuildTestCommand` should be created using the correct values.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        with patch.object(
            XcodebuildTestCommand, "__init__", return_value=None
        ) as mock_init:
            await Xctest.run_test(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
                only_testing=only_testing,
                skip_testing=skip_testing,
            )

            mock_init.assert_called_once_with(
                destination=IOSDestination(id=fake_udid),
                xctestrun=fake_xctestrun,
                only_testing=only_testing,
                skip_testing=skip_testing,
            )

    @pytest.mark.asyncio
    async def test_run_test_xcodebuild_exception(
        self,
        mock_xcodebuild_run,
        fake_udid,
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `run_test`
        AND: The xcodebuild run fails and raises a `ProcessException`

        THEN: A `ProcessException` should be raised.
        AND: The exception should contain the stdout, stderr and return code of the process.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        mock_xcodebuild_run.side_effect = ProcessException(
            stdout=["stdout"], stderr=["stderr"], return_code=1
        )

        with pytest.raises(ProcessException) as e:
            await Xctest.run_test(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
            )

        assert e.value.stdout == ["stdout"]
        assert e.value.stderr == ["stderr"]
        assert e.value.return_code == 1

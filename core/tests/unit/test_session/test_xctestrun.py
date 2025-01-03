import json
import pathlib
from unittest.mock import patch, MagicMock

import pytest

from core.exceptions.common import InvalidFileContent
from core.exceptions.xcodebuild import XcodebuildException
from core.exceptions.xctestrun import ListEnumerationFailure
from core.subprocesses.xcodebuild_command import (
    XcodebuildTestEnumerationCommand,
    IOSDestination,
)
from core.test_session.xctestrun import Xctestrun, Xctests


@pytest.fixture
def fake_tmp_file():
    return pathlib.Path("/tmp/file")


@pytest.fixture
def mock_xcodebuild_run():
    with patch(
        "core.test_session.xctestrun.Xcodebuild.run", return_value=([], [])
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
    with patch("core.test_session.xctestrun.Xctestrun._read_file") as mock:
        mock.return_value = json.dumps(success_test_enumeration_result)
        yield mock


@pytest.fixture
def mock_temporary_file_path(fake_tmp_file):
    with patch(
        "core.test_session.xctestrun.Xctestrun._temporary_file_path"
    ) as mock_context:
        mock_enter = MagicMock(return_value=fake_tmp_file)
        mock_context.return_value.__enter__ = mock_enter
        mock_context.return_value.__exit__ = MagicMock(return_value=None)

        yield mock_enter


class TestXctestrunListTests:
    """
    Test Xctestrun.list_tests method
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
        GIVEN: A Xctestrun class

        WHEN: calling `list_tests`

        THEN: A `XcodebuildTestEnumerationCommand` should be created using the correct values.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        with patch.object(
            XcodebuildTestEnumerationCommand, "__init__", return_value=None
        ) as mock_init:
            await Xctestrun.list_tests(
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
        GIVEN: A Xctestrun class

        WHEN: calling `list_tests`

        THEN: The result returned should be the same as the test enumeration result.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        result = await Xctestrun.list_tests(
            xctestrun_path=fake_xctestrun,
            destination=IOSDestination(
                id=fake_udid,
            ),
        )

        assert result == Xctests.model_validate(
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
        GIVEN: A Xctestrun class

        WHEN: calling `list_tests`
        AND: The xcodebuild run fails and raises an `XcodebuildException`

        THEN: A `XcodebuildException` should be raised.
        AND: The exception should contain the stdout, stderr and return code of the process.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"
        mock_xcodebuild_run.side_effect = XcodebuildException(
            stdout=["stdout"], stderr=["stderr"], return_code=1
        )

        with pytest.raises(XcodebuildException) as e:
            await Xctestrun.list_tests(
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
        GIVEN: A Xctestrun class

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
            await Xctestrun.list_tests(
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
        GIVEN: A Xctestrun class

        WHEN: calling `list_tests`
        AND: The xcodebuild run succeeds
        AND: The result contains no errors
        AND: The result contains more than one value

        THEN: An `InvalidFileContent` should be raised.
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"
        mock_read_file.return_value = "Invalid content"

        with pytest.raises(InvalidFileContent):
            await Xctestrun.list_tests(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
            )

import json
import pathlib
import signal
from unittest.mock import patch, MagicMock

import pytest

from core.exceptions.common import InvalidFileContent
from core.exceptions.xctest import ListEnumerationFailure
from core.subprocess import ProcessException
from core.xc.commands.xcodebuild_command import (
    XcodebuildTestEnumerationCommand,
    IOSDestination,
    XcodebuildTestCommand,
)
from core.xc.xctest import Xctest, XctestOverview


@pytest.fixture
def fake_tmp_file():
    return pathlib.Path("/tmp/file")


@pytest.fixture
def mock_xcodebuild_run():
    with patch("core.xc.xctest.async_run_process", return_value=([], [])) as run_mock:
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
    with patch("core.xc.xctest.Xctest._read_file") as mock:
        mock.return_value = json.dumps(success_test_enumeration_result)
        yield mock


@pytest.fixture
def mock_temporary_file_path(fake_tmp_file):
    with patch("core.xc.xctest.Xctest._temporary_file_path") as mock_context:
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

        # Make sure the test identifier is parsed correctly.
        assert result.enabledTests[0] == success_test_enumeration_result.get("values")[
            0
        ].get("enabledTests")[0].get("identifier")

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
                test_configuration="Some Configuration",
            )

            mock_init.assert_called_once_with(
                destination=IOSDestination(id=fake_udid),
                test_configuration="Some Configuration",
                result_bundle_path=None,
                xctestrun=fake_xctestrun,
                only_testing=only_testing,
                skip_testing=skip_testing,
            )

    @pytest.mark.asyncio
    async def test_run_test_uses_correct_signal_on_cancel(
        self, mock_xcodebuild_run, fake_udid
    ):
        """
        GIVEN: A Xctest class

        WHEN: calling `run_test`

        THEN: The `signal_on_cancel` should be set to `signal.SIGINT`
        """
        fake_xctestrun = "/tmp/some_xctestrun.xctestrun"

        with patch(
            "core.xc.xctest.XcodebuildTestCommand"
        ) as mock_xcodebuild_test_command:
            await Xctest.run_test(
                xctestrun_path=fake_xctestrun,
                destination=IOSDestination(
                    id=fake_udid,
                ),
                test_configuration="Some Configuration",
            )

            mock_xcodebuild_run.assert_called_once_with(
                command=mock_xcodebuild_test_command.return_value,
                signal_on_cancel=signal.SIGINT,
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
                test_configuration="Some Configuration",
            )

        assert e.value.stdout == ["stdout"]
        assert e.value.stderr == ["stderr"]
        assert e.value.return_code == 1

    def test_parse_xctestrun(self, example_xctestrun_path):
        """
        GIVEN: A valid xctestrun path
        AND: A Xctest class

        WHEN: calling `parse_xctestrun`

        THEN: The `TestHostPath` and `UITargetAppPath` should not contain __TESTROOT__
        AND: The `TestHostPath` and `UITargetAppPath` should contain the xctestrun parent directory path
        """
        result = Xctest.parse_xctestrun(example_xctestrun_path)

        for config in result.TestConfigurations:
            for target in config.TestTargets:
                assert "__TESTROOT__" not in target.TestHostPath
                assert str(example_xctestrun_path.parent) in target.TestHostPath
                if target.UITargetAppPath:
                    # The UITargetAppPath is optional
                    assert "__TESTROOT__" not in target.UITargetAppPath
                    assert str(example_xctestrun_path.parent) in target.UITargetAppPath

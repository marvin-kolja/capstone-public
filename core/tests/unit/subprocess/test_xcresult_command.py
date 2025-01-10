from core.subprocesses.xcresult_command import XcresultToolCommand
from tests.conftest import fake_udid


class TestXcresultToolCommand:
    """
    Tests for the xcresulttool command
    """

    def test_get_tests_structure(self, fake_udid):
        """
        GIVEN: A XcresultToolCommand class

        WHEN: calling `get_test_result_tests`
        AND: then calling `parse` on the returned command

        THEN: The correct list of strings should be returned
        """
        command = XcresultToolCommand.get_test_result_tests(
            xcresult_path="/tmp/test_results.xcresult",
        )

        parsed_command = command.parse()

        assert parsed_command == [
            "xcrun",
            "xcresulttool",
            "get",
            "test-results",
            "tests",
            "--path",
            "/tmp/test_results.xcresult",
            "--compact",
        ]

    def test_get_test_result_summary(self, fake_udid):
        """
        GIVEN: A XctraceCommand class

        WHEN: calling `get_test_result_summary`
        AND: then calling `parse` on the returned command

        THEN: The correct list of strings should be returned
        """
        command = XcresultToolCommand.get_test_result_summary(
            xcresult_path="/tmp/test_results.xcresult",
        )

        parsed_command = command.parse()

        assert parsed_command == [
            "xcrun",
            "xcresulttool",
            "get",
            "test-results",
            "summary",
            "--path",
            "/tmp/test_results.xcresult",
            "--compact",
        ]

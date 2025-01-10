import logging

from core.subprocesses.process import async_run_process
from core.subprocesses.xcresult_command import XcresultToolCommand
from core.xc.xcresult.models.test_results.summary import Summary
from core.xc.xcresult.models.test_results.tests import Tests

logger = logging.getLogger(__name__)


class XcresultTool:
    def __init__(self, xcresult_path: str):
        self.xcresult_path = xcresult_path

    @staticmethod
    async def get_raw(command: XcresultToolCommand) -> str:
        """
        Execute the xcresulttool command and return the raw output.

        :param command: The xcresulttool command to execute.
        :return: The raw output of the command.
        """
        stdout, stderr = await async_run_process(command)
        if len(stdout) != 1:
            raise ValueError(
                "Expected exactly one line of output from the xcresulttool command."
            )
        return stdout[0]

    async def get_tests(self) -> Tests:
        """
        :return: The tests structure from the xcresult file.
        """
        command = XcresultToolCommand.get_test_result_tests(self.xcresult_path)
        data = await self.get_raw(command)
        return Tests.model_validate_json(data)

    async def get_test_summary(self) -> Summary:
        """
        :return: The summary structure from the xcresult file.
        """
        command = XcresultToolCommand.get_test_result_summary(self.xcresult_path)
        data = await self.get_raw(command)
        return Summary.model_validate_json(data)

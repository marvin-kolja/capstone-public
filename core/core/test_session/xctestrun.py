import logging

from pydantic import BaseModel, Field

from core.subprocesses.xcodebuild_command import IOSDestination

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

    test_plan: str = Field(validation_alias="testPlan")
    disabled_tests: list[Xctest] = Field(validation_alias="disabledTests")
    enabled_tests: list[Xctest] = Field(validation_alias="enabledTests")


class Xctestrun:
    """
    Interactions with the xctestrun file such as listing the tests or executing them.
    """

    @staticmethod
    async def list_tests(xctestrun_path: str, destination: IOSDestination) -> Xctests:
        """
        Gets the list of tests using the xctestrun file. The xctestrun file contains the testing bundle path and testing
        host path. These are then installed on the target device, and it is checked which tests the testing bundle
        contains.

        This uses the :class:`core.subprocesses.XcodebuildTestEnumerationCommand` command to enumerate the tests.

        :param xctestrun_path: The path to the xctestrun file
        :param destination: The destination the test bundle and app is installed on.
        :return: The test enumeration result in format of the :class:`.Xctests` model`

        :raises: `XcodebuildException` when the executed command fails.
        :raises: `ListTestsFailure` when the command succeeds, but the result contains errors.
        """
        raise NotImplementedError

        # 1. Generate temporary file for results
        # 2. Execute XcodebuildTestEnumerationCommand
        # 3. Handle process errors
        # 4. Extract the result
        # 5. Handle result errors

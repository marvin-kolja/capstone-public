import logging
import pathlib

from pydantic import BaseModel

from core.subprocess import async_run_process, ProcessException
from core.xc.commands.xcodebuild_command import (
    XcodebuildListCommand,
    XcodebuildShowTestPlansCommand,
)

logger = logging.getLogger(__name__)


class ProjectDetails(BaseModel):
    """
    Details of an xcode project.
    """

    configurations: list[str]
    name: str
    schemes: list[str]
    targets: list[str]


class XcListProjectResult(BaseModel):
    """
    Result of listing an xcode project.
    """

    project: ProjectDetails


class XcShowTestPlansResult(BaseModel):
    """
    Test plans result from `xcodebuild -showTestPlans -json` command.
    """

    class __XcTestPlan(BaseModel):
        """
        Xcode test plan.
        """

        name: str

    testPlans: list[__XcTestPlan]


class XcProject:
    """
    Methods to interact with an Xcode project.
    """

    def __init__(self, path_to_project: str):
        if not path_to_project.endswith(".xcodeproj"):
            error_msg = (
                f"Path to project must end with .xcodeproj, but got {path_to_project}"
            )
            logger.error(error_msg)
            raise ValueError(
                error_msg,
            )
        if not pathlib.Path(path_to_project).exists():
            error_msg = f"Path to project does not exist: {path_to_project}"
            logger.error(error_msg)
            raise FileNotFoundError(
                error_msg,
            )

        self.path_to_project = path_to_project

    async def list(self) -> ProjectDetails:
        """
        Lists the targets, configurations, and schemes of the project.

        :return: Project details
        :raises ProcessException: when the executed command fails
        :raises ValidationError: when the output of the command cannot be parsed correctly
        """
        logger.debug(f"Listing project details for {self.path_to_project}")

        command = XcodebuildListCommand(
            project=self.path_to_project,
            json_output=True,
        )

        try:
            stdout, stderr = await async_run_process(command=command)
        except ProcessException as e:
            logger.error(
                f"Command to list project details of {self.path_to_project} failed: {e}"
            )
            raise

        try:
            json_string = "".join(stdout)
            return XcListProjectResult.model_validate_json(json_string).project
        except Exception as e:
            logger.error(
                f"Failed to parse project details of {self.path_to_project}: {e}"
            )
            raise

    async def xcode_test_plans(self, scheme: str) -> [str]:
        """
        Get the test plans from the given project.

        :param scheme: The project scheme to get the test plans for
        :return: Names of the test plans as a list
        :raises ProcessException: when the executed command fails
        :raises ValidationError: when the output of the command cannot be parsed correctly
        """
        logger.debug(f"Getting test plans for project {self.path_to_project}")

        command = XcodebuildShowTestPlansCommand(
            project=self.path_to_project,
            scheme=scheme,
            json_output=True,
        )

        try:
            stdout, _ = await async_run_process(command=command)
        except ProcessException as e:
            logger.error(f"Failed to get the test plans of {self.path_to_project}: {e}")
            raise

        try:
            json_string = "".join(stdout)
            result = XcShowTestPlansResult.model_validate_json(json_string)
            return [test_plan.name for test_plan in result.testPlans]
        except Exception as e:
            logger.error(
                f"Failed to parse the output of the test plans of {self.path_to_project}: {e}"
            )
            raise

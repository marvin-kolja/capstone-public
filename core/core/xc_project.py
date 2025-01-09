import logging

from pydantic import BaseModel

from core.subprocesses.process import async_run_process

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
        self.path_to_project = path_to_project

    async def list(self) -> ProjectDetails:
        """
        Lists the targets, configurations, and schemes of the project.

        :return: Project details
        :raises ProcessException: when the executed command fails
        :raises ValidationError: when the output of the command cannot be parsed correctly
        """
        # TODO: use async_run_process to execute XcodebuildListCommand
        raise NotImplementedError

    async def xcode_test_plans(self) -> [str]:
        """
        Get the test plans from the given project.

        :return: Names of the test plans as a list
        :raises ProcessException: when the executed command fails
        :raises ValidationError: when the output of the command cannot be parsed correctly
        """
        # TODO: use async_run_process to execute XcodebuildShowTestPlansCommand
        raise NotImplementedError

import logging
import pathlib
from typing import Optional, Literal

from pydantic import BaseModel

from core.subprocess import async_run_process, ProcessException
from core.xc.commands.xcodebuild_command import (
    IOSDestination,
    XcodebuildBuildCommand,
)
from core.xc.xc_project import XcProject

logger = logging.getLogger(__name__)


class XcodeBuildArtefacts(BaseModel):
    """
    The result of building an xcode project.
    """

    build_dir: str
    """The directory where the build artifacts are stored."""
    products_dir: str
    """The directory where the build products are stored such as xctestrun files."""
    iphoneos_dir: str
    """The directory where the configuration specific build products for the iphoneos platform are stored."""
    configuration: str
    """The configuration used for the build."""
    scheme: str
    """The scheme used for the build"""


class XcodeTestBuildArtefacts(XcodeBuildArtefacts):
    """
    The result of building an xcode project for testing.
    """

    xctestrun_path: str
    """The path to the xctestrun file."""
    test_plan: str
    """The xcode test plan used for the build."""


class AppBuilder:
    """
    Handles building applications using e.g. xcodebuild

    Attributes:
        xc_project (XcProject): The xcode project to build on.
    """

    def __init__(self, xc_project: XcProject):
        """
        :param xc_project: The xcode project to build on.
        """
        self.xc_project: XcProject = xc_project

    async def build(
        self,
        scheme: str,
        configuration: str,
        destination: IOSDestination,
        output_dir: str,
        clean: Optional[bool] = False,
    ) -> XcodeBuildArtefacts:
        """
        Builds the application of the given xcode project

        :param scheme: The scheme to build.
        :param configuration: The configuration to build.
        :param destination: The destination to build for.
        :param output_dir: The directory to store the build artifacts.
        :param clean: Whether to clean the build directory before building. Default is False.
        """
        actions: list[Literal["clean", "build"]] = ["build"]
        if clean:
            actions.insert(0, "clean")

        command = XcodebuildBuildCommand(
            actions=actions,
            project=self.xc_project.path_to_project,
            scheme=scheme,
            configuration=configuration,
            destination=destination,
            derived_data_path=output_dir,
        )

        try:
            await async_run_process(command=command)
        except ProcessException as e:
            logger.error(f"Failed to build xcode project: {e}")
            raise

        logger.debug(
            f"Successfully built xcode project: {self.xc_project.path_to_project}"
        )

        return XcodeBuildArtefacts(
            build_dir=self.build_dir(output_dir).as_posix(),
            products_dir=self.products_dir(output_dir).as_posix(),
            iphoneos_dir=self.iphoneos_dir(output_dir, configuration).as_posix(),
            configuration=configuration,
            scheme=scheme,
        )

    async def build_for_testing(
        self,
        scheme: str,
        configuration: str,
        destination: IOSDestination,
        test_plan: str,
        output_dir: str,
        clean: Optional[bool] = False,
    ) -> XcodeTestBuildArtefacts:
        """
        Build xcode project for testing

        :param scheme: The scheme to build.
        :param configuration: The configuration to build.
        :param destination: The destination to build for.
        :param test_plan: The xcode test plan to use.
        :param output_dir: The directory to store the build artifacts.
        :param clean: Whether to clean the build directory before building. Default is False.
        """
        actions: list[Literal["clean", "build-for-testing"]] = ["build-for-testing"]
        if clean:
            actions.insert(0, "clean")

        command = XcodebuildBuildCommand(
            actions=actions,
            project=self.xc_project.path_to_project,
            scheme=scheme,
            configuration=configuration,
            destination=destination,
            derived_data_path=output_dir,
            test_plan=test_plan,
        )

        try:
            await async_run_process(command=command)
        except ProcessException as e:
            logger.error(f"Failed to build xcode project: {e}")
            raise

        logger.debug(
            f"Successfully built xcode project for testing: {self.xc_project.path_to_project}"
        )

        return XcodeTestBuildArtefacts(
            build_dir=self.build_dir(output_dir).as_posix(),
            products_dir=self.products_dir(output_dir).as_posix(),
            iphoneos_dir=self.iphoneos_dir(output_dir, configuration).as_posix(),
            configuration=configuration,
            scheme=scheme,
            xctestrun_path=self.xctestrun_file(
                output_dir, scheme, test_plan
            ).as_posix(),
            test_plan=test_plan,
        )

    @staticmethod
    def build_dir(base_dir: str) -> pathlib.Path:
        """
        Get the directory where the build artifacts are stored relative to the base directory.
        :param base_dir: The base directory where the build artifacts are stored.
        """
        return pathlib.Path(
            base_dir,
            "Build",
        )

    @staticmethod
    def products_dir(base_dir: str) -> pathlib.Path:
        """
        Get the directory where the build products are stored relative to the base directory.
        :param base_dir: The base directory where the build artifacts are stored.
        """
        return pathlib.Path(
            AppBuilder.build_dir(base_dir),
            "Products",
        )

    @staticmethod
    def iphoneos_dir(base_dir: str, configuration: str) -> pathlib.Path:
        """
        Get the directory where the build products for the iphoneos platform are stored for the given configuration
        relative to the base directory.
        :param base_dir: The base directory where the build artifacts are stored.
        :param configuration: The configuration used for the build.
        """
        return pathlib.Path(
            AppBuilder.products_dir(base_dir),
            f"{configuration}-iphoneos",
        )

    @staticmethod
    def xctestrun_file(base_dir: str, scheme: str, test_plan: str) -> pathlib.Path:
        """
        Get the path to the xctestrun file relative to the products directory relative to the base directory.
        :param base_dir: The base directory where the build artifacts are stored.
        :param scheme: The scheme used for the build.
        :param test_plan: The test plan used for the build.
        """
        products_dir = AppBuilder.products_dir(base_dir)
        xctestrun_files = list(products_dir.glob("*.xctestrun"))

        logger.debug(f"Found xctestrun files: {xctestrun_files}")
        logger.debug(f"Looking for xctestrun file with prefix: {scheme}_{test_plan}")

        matching_xctestrun_files = [
            xctestrun_file
            for xctestrun_file in xctestrun_files
            if xctestrun_file.name.startswith(f"{scheme}_{test_plan}")
        ]

        if len(matching_xctestrun_files) != 1:
            logger.error(
                f"Expected to find 1 matching xctestrun file, but found {len(matching_xctestrun_files)}."
            )
            raise FileNotFoundError(
                "Expected to find 1 matching xctestrun file, but found none or multiple."
            )

        return xctestrun_files[0]

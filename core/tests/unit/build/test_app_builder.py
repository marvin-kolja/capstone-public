import pathlib
from unittest.mock import patch, MagicMock

import pytest

from core.build.app_builder import AppBuilder
from core.subprocesses.process import Process
from core.subprocesses.xcodebuild_command import IOSDestination
from core.xc_project import XcProject


@pytest.fixture
def mock_xc_project():
    mock = MagicMock(spec=XcProject)
    mock.path_to_project = "path/to/project.xcodeproj"
    return mock


class TestAppBuilder:
    @pytest.mark.asyncio
    async def test_build(self, mock_xc_project):
        """
        GIVEN: An XcProject

        WHEN: The build method is called

        THEN: The build artefacts are returned.
        """
        app_builder = AppBuilder(mock_xc_project)
        scheme = "scheme1"
        configuration = "config1"
        destination = MagicMock(spec=IOSDestination)
        output_dir = "/tmp/output"

        with patch("core.subprocesses.process.Process") as mock_process:
            mock_process_instance = MagicMock(spec=Process)
            mock_process_instance.failed = False
            mock_process_instance.execute.return_value = None
            mock_process_instance.wait.return_value = ([], [])
            mock_process.return_value = mock_process_instance

            result = await app_builder.build(
                scheme=scheme,
                configuration=configuration,
                destination=destination,
                output_dir=output_dir,
            )

            mock_process_instance.execute.assert_awaited_once()
            mock_process_instance.wait.assert_awaited()

            assert result.build_dir == "/tmp/output/Build"
            assert result.products_dir == "/tmp/output/Build/Products"
            assert result.iphoneos_dir == "/tmp/output/Build/Products/config1-iphoneos"
            assert result.configuration == configuration
            assert result.scheme == scheme

    @pytest.mark.asyncio
    async def test_build_for_testing(self, mock_xc_project):
        """
        GIVEN: An XcProject

        WHEN: The build_for_testing method is called

        THEN: The project details are returned.
        """
        app_builder = AppBuilder(mock_xc_project)
        scheme = "scheme1"
        configuration = "config1"
        destination = MagicMock(spec=IOSDestination)
        output_dir = "/tmp/output"
        test_plan = "testPlan1"

        with patch("core.subprocesses.process.Process") as mock_process, patch.object(
            app_builder, "xctestrun_file"
        ) as mock_xctestrun_file:
            mock_process_instance = MagicMock(spec=Process)
            mock_process_instance.failed = False
            mock_process_instance.execute.return_value = None
            mock_process_instance.wait.return_value = ([], [])
            mock_process.return_value = mock_process_instance

            mock_xctestrun_file.return_value = pathlib.Path(
                "/tmp/output/Build/Products/scheme1_testPlan1_other_file_name_content.xctestrun"
            )

            result = await app_builder.build_for_testing(
                scheme=scheme,
                configuration=configuration,
                destination=destination,
                output_dir=output_dir,
                test_plan=test_plan,
            )

            mock_process_instance.execute.assert_awaited_once()
            mock_process_instance.wait.assert_awaited()

            assert result.build_dir == "/tmp/output/Build"
            assert result.products_dir == "/tmp/output/Build/Products"
            assert result.iphoneos_dir == "/tmp/output/Build/Products/config1-iphoneos"
            assert result.configuration == configuration
            assert result.scheme == scheme
            assert (
                result.xctestrun_path
                == "/tmp/output/Build/Products/scheme1_testPlan1_other_file_name_content.xctestrun"
            )
            assert result.test_plan == test_plan

    def test_build_dir(self):
        """
        GIVEN: A directory path

        WHEN: The build_dir method is called

        THEN: A pathlib Path object is returned with the directory path appended with "Build"
        """

        base_dir = "/tmp/base_dir"
        expected = "/tmp/base_dir/Build"

        result = AppBuilder.build_dir(base_dir).as_posix()
        assert result == expected

    def test_products_dir(self):
        """
        GIVEN: A directory path

        WHEN: The products_dir method is called

        THEN: A pathlib Path object is returned with the directory path appended with "Build/Products"
        """

        base_dir = "/tmp/base_dir"
        expected = "/tmp/base_dir/Build/Products"

        result = AppBuilder.products_dir(base_dir).as_posix()
        assert result == expected

    def test_iphoneos_dir(self):
        """
        GIVEN: A directory path and a configuration

        WHEN: The iphoneos_dir method is called

        THEN: A pathlib Path object is returned with the directory path appended with "Build/Products/{configuration}-iphoneos"
        """
        base_dir = "/tmp/base_dir"
        configuration = "Release"
        expected = "/tmp/base_dir/Build/Products/Release-iphoneos"

        result = AppBuilder.iphoneos_dir(base_dir, configuration).as_posix()
        assert result == expected

    def test_xctestrun_file(self):
        """
        GIVEN: A directory path, a scheme, and an xcode test plan name

        WHEN: The xctestrun_file method is called

        THEN: A pathlib Path object is returned with the directory path appended with "Build/Products/*.xctestrun"
        """
        base_dir = "/tmp/base_dir"
        scheme = "TestScheme"
        test_plan = "TestPlan"
        expected = "/tmp/base_dir/Build/Products/TestScheme_TestPlan_other_file_name_content.xctestrun"

        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = [
                pathlib.Path(expected),
                pathlib.Path("/tmp/base_dir/Build/Products/another.xctestrun"),
            ]
            result = AppBuilder.xctestrun_file(base_dir, scheme, test_plan).as_posix()

            assert result == expected

from unittest.mock import patch, MagicMock

import pytest

from core.subprocesses.process import Process
from core.xc_project import XcProject


class TestXcProject:

    def test_init_path_to_project_ends_with_xcodeproj(self):
        """
        GIVEN: A path to an xcode project that does not end with .xcodeproj

        WHEN: The XcProject is initialized

        THEN: A ValueError is raised.
        """
        with pytest.raises(ValueError):
            XcProject("path/to/project")

    @pytest.mark.asyncio
    async def test_list(self):
        """
        GIVEN: An XcProject

        WHEN: The list method is called

        THEN: The project details are returned.
        """
        project = XcProject("path/to/project.xcodeproj")

        example_stdout = [
            "{",
            '  "project": {',
            '    "configurations": ["config1"],',
            '    "name": "project",',
            '    "schemes": ["scheme1"],',
            '    "targets": ["target1"]',
            "  }",
            "}",
        ]

        with patch("core.subprocesses.process.Process") as mock_process:
            mock_process_instance = MagicMock(spec=Process)
            mock_process_instance.failed = False
            mock_process_instance.execute.return_value = None
            mock_process_instance.wait.return_value = (example_stdout, [])
            mock_process.return_value = mock_process_instance

            result = await project.list()

            assert result.configurations == ["config1"]
            assert result.name == "project"
            assert result.schemes == ["scheme1"]
            assert result.targets == ["target1"]

    @pytest.mark.asyncio
    async def test_xcode_test_plans(self):
        """
        GIVEN: An XcProject

        WHEN: The xcode_test_plans method is called

        THEN: The test plans are returned.
        """
        project = XcProject("path/to/project.xcodeproj")

        example_stdout = [
            "{",
            '  "testPlans": [',
            "    {",
            '      "name": "testPlan1"',
            "    }",
            "  ]",
            "}",
        ]

        with patch("core.subprocesses.process.Process") as mock_process:
            mock_process_instance = MagicMock(spec=Process)
            mock_process_instance.failed = False
            mock_process_instance.execute.return_value = None
            mock_process_instance.wait.return_value = (example_stdout, [])
            mock_process.return_value = mock_process_instance

            result = await project.xcode_test_plans()

            assert result == ["testPlan1"]

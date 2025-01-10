import pathlib

import pytest

from core.xc.xcresult.models.test_results.summary import Summary
from core.xc.xcresult.models.test_results.tests import Tests
from core.xc.xcresult.xcresulttool import XcresultTool


@pytest.fixture
def example_xcresult_path():
    current_path = pathlib.Path(__file__).parent
    return current_path / ".." / ".." / "test_data" / "Example.xcresult"


class TestXcresultTool:
    @pytest.mark.asyncio
    async def test_get_tests(self, example_xcresult_path):
        """
        GIVEN: A path to a xcresult package

        WHEN: get_tests is called

        THEN: A Tests object is returned
        """
        xcresult_tool = XcresultTool(xcresult_path=example_xcresult_path.as_posix())
        tests = await xcresult_tool.get_tests()
        assert isinstance(tests, Tests)

    @pytest.mark.asyncio
    async def test_get_test_summary(self, example_xcresult_path):
        """
        GIVEN: A path to a xcresult package

        WHEN: get_test_summary is called

        THEN: A Summary object is returned
        """

        xcresult_tool = XcresultTool(xcresult_path=example_xcresult_path.as_posix())
        summary = await xcresult_tool.get_test_summary()
        assert isinstance(summary, Summary)

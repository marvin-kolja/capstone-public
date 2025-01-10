import pathlib

import pytest


@pytest.fixture
def example_xcresult_path():
    current_path = pathlib.Path(__file__).parent
    return current_path / ".." / ".." / "test_data" / "Example.xcresult"


class TestXcresultTool:
    @pytest.mark.asyncio
    async def test_get_tests(self, example_xcresult_path):
        from core.xcresult.xcresulttool import XcresultTool

        xcresult_tool = XcresultTool(xcresult_path=example_xcresult_path.as_posix())
        tests = await xcresult_tool.get_tests()

    @pytest.mark.asyncio
    async def test_get_test_summary(self, example_xcresult_path):
        from core.xcresult.xcresulttool import XcresultTool

        xcresult_tool = XcresultTool(xcresult_path=example_xcresult_path.as_posix())
        summary = await xcresult_tool.get_test_summary()

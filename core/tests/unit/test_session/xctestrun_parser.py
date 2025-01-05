from core.test_session.xctestrun_parser import parse_xctestrun_content


class TestParseXctestrunContent:
    def test_valid_xctestrun(self, example_xctestrun_content):
        """
        GIVEN valid xctestrun content

        WHEN the content is parsed

        THEN the xctestrun file should be parsed successfully
        """
        parse_xctestrun_content(example_xctestrun_content)

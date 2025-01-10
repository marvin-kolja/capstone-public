from core.subprocesses.process import ProcessCommand


class XcresultToolCommand(ProcessCommand):
    """
    A command parser to interact with the xcresulttool command.
    """

    def __init__(self, xcresult_path: str, get_options: list[str]):
        self.xcresult_path = xcresult_path
        self.get_options = get_options

    def parse(self) -> list[str]:
        return [
            "xcrun",
            "xcresulttool",
            "get",
            *self.get_options,
            "--path",
            self.xcresult_path,
            "--compact",  # This way the output is just one line
        ]

    @classmethod
    def get_test_result_tests(cls, xcresult_path: str):
        """
        Gets the tests structure from the test results.
        """
        return cls(xcresult_path, ["test-results", "tests"])

    @classmethod
    def get_test_result_summary(cls, xcresult_path: str):
        """
        Gets the summary from the test results.
        """
        return cls(xcresult_path, ["test-results", "summary"])

from core.exceptions.xcodebuild import XcodebuildException
from core.subprocesses.process import Process
from core.subprocesses.xcodebuild_command import XcodebuildCommand


class Xcodebuild:
    """
    Exposes certain methods to execute xcodebuild commands (core.subprocesses.xcodebuild_command).
    """

    @staticmethod
    async def run(command: XcodebuildCommand) -> tuple[list[str], list[str]]:
        """
        Runs the xcodebuild command in a subprocess.

        :param command: The xcodebuild command to execute.

        :return: The stdout and stderr of the xcodebuild command `(stdout, stderr)`.

        :raises XcodebuildException: If the xcodebuild command failed with a non-zero return code.
        """
        process = Process(command=command)
        await process.execute()
        stdout, stderr = await process.wait()

        if process.failed:
            raise XcodebuildException(
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
            )

        return stdout, stderr

import asyncio
import atexit
import os
import signal
from abc import ABC, abstractmethod
from asyncio import subprocess
from typing import Optional


class ProcessCommand(ABC):
    """
    Used by the `Process` class to parse the command
    """

    @abstractmethod
    def parse(self) -> [str]:
        """
        Parse the command to be executed by the `Process` class.
        :return: A list of strings representing the command.
        """
        ...


class ProcessError(Exception):
    """ Base class for all exceptions process related. """


class CommandError(ProcessError):
    """ Raised when the command is invalid. """


class ProcessAlreadyRunningError(ProcessError):
    """ Raised when trying to start a process that is already running. """


class Process:
    """
    A wrapper around the `asyncio.create_subprocess_exec` to make it easier to execute commands.

    The main functionalities are:
        - Execute a command in a subprocess
        - Ability to terminate or kill the process
        - Checking the status of the process
        - Getting the return code of the process
        - Waiting for the process to finish
            - Exposes the stdout and stderr as lists of strings
    """

    def __init__(self, command: ProcessCommand):
        """
        :param command: The command to be executed by the process.
        """
        if not isinstance(command, ProcessCommand):
            raise CommandError(f"Invalid command: {command}")
        self.__command = command
        self.__process: Optional[subprocess.Process] = None

    @property
    def command(self) -> ProcessCommand:
        return self.__command

    @property
    def returncode(self) -> Optional[int]:
        if self.__process is None:
            return None
        return self.__process.returncode

    @property
    def is_running(self) -> bool:
        return self.__process is not None and self.returncode is None

    @property
    def terminated(self) -> bool:
        return self.__process is not None and self.returncode is not None

    @property
    def failed(self) -> bool:
        if self.terminated:
            return self.__process.returncode != 0
        return False

    async def execute(self, cwd: Optional[str] = None):
        """
        Execute the command in an asyncio subprocess.

        :param cwd: The working directory to execute the command in.

        :raises ProcessAlreadyRunningError: If the process is already running.
        """
        if self.is_running:
            raise ProcessAlreadyRunningError()

        args = self.command.parse()

        self.__process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        atexit.register(self.kill)

    def terminate(self):
        if self.is_running:
            self._send_signal(self.__process.pid, signal.SIGTERM)

    def kill(self):
        if self.is_running:
            self._send_signal(self.__process.pid, signal.SIGKILL)

    async def wait(self) -> tuple[[str], [str]]:
        """
        Wait for the process to finish and return the stdout and stderr as a tuple.

        :return: A tuple containing the stdout and stderr as lists of strings.
        """
        if self.is_running:
            stdout = await self._read_stream(self.__process.stdout)
            stderr = await self._read_stream(self.__process.stderr)
            await self.__process.wait()
            return stdout, stderr

    @staticmethod
    async def _read_stream(stream: asyncio.StreamReader) -> list[str]:
        """
        Read a stream, line by line and decode it.
        """
        lines = []
        while True:
            line = await stream.readline()
            if not line:  # EOF, no more lines to read
                break
            decoded_line = line.decode().strip()
            lines.append(decoded_line)
        return lines

    @staticmethod
    def _send_signal(pid: int, sig: signal.Signals):
        """ Uses the `os.kill` to send a signal to the process group. """
        os.kill(pid, sig)

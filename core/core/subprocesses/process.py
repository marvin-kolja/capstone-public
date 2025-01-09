import asyncio
import atexit
import logging
import os
import signal
from abc import ABC, abstractmethod
from asyncio import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


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
    """Base class for all exceptions process related."""


class CommandError(ProcessError):
    """Raised when the command is invalid."""


class ProcessAlreadyRunningError(ProcessError):
    """Raised when trying to start a process that is already running."""


class ProcessException(ProcessError):
    """Raised when the process failed with a non-zero return code."""

    def __init__(self, stdout: [str], stderr: [str], return_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        super().__init__(f"Process failed with return code: {return_code}")


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
            logger.critical(
                f"Provided command is not an instance of ProcessCommand: {command.__class__.__name__}"
            )
            raise CommandError()
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
            return self.returncode != 0
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
        logger.info(f"Executing command: {' '.join(args)}")

        self.__process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.debug(f"Process started with PID: {self.__process.pid}")

        atexit.register(self.kill)
        logger.debug("Registered kill at exit handler")

    def terminate(self):
        if self.is_running:
            self._send_signal(self.__process.pid, signal.SIGTERM)

    def kill(self):
        if self.is_running:
            self._send_signal(self.__process.pid, signal.SIGKILL)

    def send_signal(self, sig: signal.Signals):
        if self.is_running:
            self._send_signal(self.__process.pid, sig)

    async def wait(self) -> tuple[list[str], list[str]]:
        """
        Wait for the process to finish and return the stdout and stderr as a tuple.

        :return: A tuple containing the stdout and stderr as lists of strings.
        """
        if self.is_running:
            stdout = await self._read_stream(self.__process.stdout)
            stderr = await self._read_stream(self.__process.stderr)
            logger.debug("Waiting for process to finish")
            await self.__process.wait()
            logger.debug("Process finished")
            atexit.unregister(self.kill)
            logger.debug("Unregistered kill at exit handler")
            return stdout, stderr
        return [], []

    @staticmethod
    async def _read_stream(stream: asyncio.StreamReader) -> list[str]:
        """
        Read a stream, line by line and decode it.
        """
        lines = []
        while True:
            line = await stream.readline()
            if not line:  # EOF, no more lines to read
                logger.debug("EOF reached, no more lines to read")
                break
            decoded_line = line.decode().strip()
            logger.debug(f"Read line new line from stream: {decoded_line}")
            lines.append(decoded_line)
        return lines

    @staticmethod
    def _send_signal(pid: int, sig: signal.Signals):
        """Uses the `os.kill` to send a signal to the process group."""
        logger.debug(f"Sending {sig} to process with PID: {pid}")
        os.kill(pid, sig)


async def async_run_process(
    command: ProcessCommand,
    cwd: Optional[str] = None,
    signal_on_cancel: signal.Signals = signal.SIGTERM,
) -> tuple[list[str], list[str]]:
    """
    Convenience function to run a command using the `Process` class. It will create a new `Process` instance, execute
    the command and wait for the process to finish.

    If CancelledError is raised, the process will be terminated with the signal provided in `signal_on_cancel`.

    :param command: The command to execute.
    :param cwd: The working directory to execute the command in.
    :param signal_on_cancel: The signal to send to the process if the execution is cancelled.

    :return: The stdout and stderr of the command `(stdout, stderr)`.

    :raises ProcessException: If the process failed with a non-zero return code.
    """
    process = Process(command=command)

    std_out_err: Optional[tuple[list[str], list[str]]] = None

    async def wait():
        nonlocal std_out_err
        local_std_out_err = await process.wait()
        if std_out_err is None:
            std_out_err = local_std_out_err
        if process.failed:
            raise ProcessException(
                stdout=std_out_err[0],
                stderr=std_out_err[1],
                return_code=process.returncode,
            )

    try:
        await process.execute(cwd=cwd)
        await wait()
    except asyncio.CancelledError:
        logger.debug("Process execution was cancelled")
        process.send_signal(signal_on_cancel)
    finally:
        await wait()
        return std_out_err

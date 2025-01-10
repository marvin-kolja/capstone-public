import asyncio
import signal
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from core.subprocess import (
    CommandError,
    Process,
    ProcessCommand,
    ProcessAlreadyRunningError,
    async_run_process,
    ProcessException,
)


@pytest.fixture
def mock_asyncio_process():
    with patch("asyncio.subprocess.Process") as mock:
        mock_instance = AsyncMock(wraps=asyncio.subprocess.Process)
        mock.return_value = mock_instance

        yield mock_instance


@pytest.fixture
def mock_asyncio_create_subprocess_exec(mock_asyncio_process):
    with patch("asyncio.create_subprocess_exec") as mock:
        mock.return_value = mock_asyncio_process

        yield mock


@pytest.fixture
def mock_os_kill():
    with patch("os.kill") as mock:
        yield mock


@pytest.fixture
def dummy_command():
    class DummyCommand(ProcessCommand):
        def parse(self) -> [str]:
            return []

    return DummyCommand()


@pytest.fixture
def process(dummy_command):
    return Process(command=dummy_command)


class TestProcess:
    def test_init_invalid_command(self):
        """
        GIVEN: An invalid command

        WHEN: Trying to create a new Process instance

        THEN: The CommandError exception should be raised
        """

        class InvalidCommand:
            pass

        with pytest.raises(CommandError):
            Process(command=InvalidCommand())

    @pytest.mark.asyncio
    async def test_execute(self, mock_asyncio_create_subprocess_exec, process):
        """
        GIVEN: A Process instance

        WHEN: Trying to execute it

        THEN: The command should be parsed
        AND: The `asyncio.create_subprocess_exec` should be called
        AND: The subprocess process should be stored in the instance
        """
        with patch.object(
            process.command, "parse", wraps=process.command.parse
        ) as spied_parse:
            await process.execute()

            spied_parse.assert_called_once()
            mock_asyncio_create_subprocess_exec.assert_awaited_once()
            assert process._Process__process is not None

    @pytest.mark.asyncio
    async def test_execute_already_running(self, mock_asyncio_process, process):
        """
        GIVEN: A Process instance
        AND: A subprocess process that is already running

        WHEN: Trying to execute it

        THEN: The ProcessAlreadyRunningError exception should be raised
        """
        process._Process__process = mock_asyncio_process
        mock_asyncio_process.returncode = None

        with pytest.raises(ProcessAlreadyRunningError):
            await process.execute()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name, sig", [("terminate", signal.SIGTERM), ("kill", signal.SIGKILL)]
    )
    async def test_stopping(
        self, mock_asyncio_process, mock_os_kill, process, method_name, sig
    ):
        """
        GIVEN: A Process instance
        AND: A subprocess process that is running

        WHEN: Trying to stop the process

        THEN: The `os.kill` should be called with the correct signal
        """
        process._Process__process = mock_asyncio_process
        mock_asyncio_process.returncode = None

        method = getattr(process, method_name)
        method()

        mock_os_kill.assert_called_once_with(mock_asyncio_process.pid, sig)

    @pytest.mark.asyncio
    async def test_atexist_handler_registered(
        self, mock_asyncio_create_subprocess_exec, mock_asyncio_process, process
    ):
        """
        GIVEN: A Process instance

        WHEN: The process is executed

        THEN: The `atexit.register` should be called with the `kill` method
        """
        with patch("atexit.register") as mock_atexit_register:
            await process.execute()

            mock_atexit_register.assert_called_once_with(process.kill)

    @pytest.mark.asyncio
    async def test_atexist_handler_unregistered(self, mock_asyncio_process, process):
        """
        GIVEN: A Process instance
        AND: A mocked asyncio subprocess process
        AND: A mocked `_read_stream` method

        WHEN: The process is waited for

        THEN: The `atexit.unregister` should be called with the `kill` method
        """
        with patch("atexit.unregister") as mock_atexit_unregister:
            process._Process__process = mock_asyncio_process
            mock_asyncio_process.returncode = None
            with patch.object(process, "_read_stream", AsyncMock(return_value=[])):

                await process.wait()

            mock_atexit_unregister.assert_called_once_with(process.kill)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "returncode, expected", [(-1, True), (0, False), (1, True)]
    )
    async def test_failed_property(
        self, returncode, expected, mock_asyncio_process, process
    ):
        """
        GIVEN: A process instance
        AND: The subprocess process has terminated with a returncode

        WHEN: Accessing the `failed` property

        THEN: The correct value should be returned
        """
        process._Process__process = mock_asyncio_process
        mock_asyncio_process.returncode = returncode

        assert process.failed == expected

    @pytest.mark.asyncio
    async def test_wait(self, mock_asyncio_process, process):
        """
        GIVEN: A process instance
        AND: Mocked asyncio subprocess process
        AND: Simulated stdout and stderr streams

        WHEN: Calling the `wait` method

        THEN: The `asyncio.subprocess.Process.wait` should be called
        AND: The stdout and stderr streams should be parsed correctly
        """
        process._Process__process = mock_asyncio_process
        mock_asyncio_process.returncode = None
        line = "line1"
        stream_line = f"{line}\n".encode()
        stream_content = [stream_line, b""]

        stdout_stream_reader = MagicMock(spec=asyncio.StreamReader)
        stdout_stream_reader.readline = AsyncMock(side_effect=stream_content)
        stderr_stream_reader = MagicMock(spec=asyncio.StreamReader)
        stderr_stream_reader.readline = AsyncMock(side_effect=stream_content)

        mock_asyncio_process.stdout = stdout_stream_reader
        mock_asyncio_process.stderr = stderr_stream_reader

        stdout, stderr = await process.wait()

        mock_asyncio_process.wait.assert_awaited_once()
        assert stdout == [line]
        assert stderr == [line]

    @pytest.mark.asyncio
    async def test_wait_not_running(self, process):
        """
        GIVEN: A process instance

        WHEN: Calling the `wait` method

        THEN: The method should return empty lists
        """
        stdout, stderr = await process.wait()

        assert stdout == []
        assert stderr == []

    @pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGKILL, signal.SIGINT])
    @pytest.mark.asyncio
    async def test_send_signal(self, mock_asyncio_process, mock_os_kill, process, sig):
        """
        GIVEN: A process instance
        AND: A mocked asyncio subprocess process

        WHEN: Sending a signal to the process

        THEN: The `os.kill` should be called with the correct signal
        """
        process._Process__process = mock_asyncio_process
        mock_asyncio_process.returncode = None

        process.send_signal(sig)

        mock_os_kill.assert_called_once_with(mock_asyncio_process.pid, sig)


async def test_async_run_process_cancel():
    """
    GIVEN: A command that is running using the `async_run_process` function inside a task

    WHEN: The task is cancelled

    THEN: The process should signal to close with the given signal
    AND: The process should be waited correctly
    """
    command = MagicMock(spec=ProcessCommand)

    async def sleep(*args, **kwargs):
        await asyncio.sleep(0.1)

    with patch("core.subprocess.Process") as mock_process:
        mock_process_instance = AsyncMock(spec=Process)
        mock_process_instance.failed = False
        mock_process_instance.execute.side_effect = sleep
        mock_process_instance.wait.side_effect = sleep
        mock_process.return_value = mock_process_instance

        task = asyncio.create_task(
            async_run_process(command=command, signal_on_cancel=signal.SIGKILL)
        )
        await asyncio.sleep(0.15)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        mock_process_instance.send_signal.assert_called_once()
        mock_process_instance.wait.assert_awaited()
        assert mock_process_instance.wait.await_count == 2
        mock_process_instance.send_signal.assert_called_once_with(signal.SIGKILL)


async def test_async_run_process_exception():
    """
    GIVEN: A command that is running using the `async_run_process` function

    WHEN: The `execute` method of the process raises an exception

    THEN: The exception should be raised from the task after the process was awaited.
    """
    command = MagicMock(spec=ProcessCommand)

    async def sleep(*args, **kwargs):
        await asyncio.sleep(0.1)

    with patch("core.subprocess.Process") as mock_process:
        mock_process_instance = AsyncMock(spec=Process)
        mock_process_instance.failed = False
        mock_process_instance.execute.side_effect = ValueError
        mock_process_instance.wait.side_effect = sleep
        mock_process.return_value = mock_process_instance

        with pytest.raises(ValueError):
            await async_run_process(command=command)

        mock_process_instance.wait.assert_awaited_once()


async def test_async_run_process_failed():
    """
    GIVEN: A command that is running using the `async_run_process` function

    WHEN: The process fails

    THEN: The `ProcessException` should be raised
    """
    command = MagicMock(spec=ProcessCommand)

    with patch("core.subprocess.Process") as mock_process:
        mock_process_instance = AsyncMock(spec=Process)
        mock_process_instance.failed = True
        mock_process.return_value = mock_process_instance

        with pytest.raises(ProcessException):
            await async_run_process(command=command)

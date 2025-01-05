import pytest


@pytest.fixture
async def tunnel_server_subprocess(port):
    from core.subprocesses.tunnel_server_command import TunnelServerCommand
    from core.subprocesses.process import Process

    command = TunnelServerCommand(port=port)
    process = Process(command)
    await process.execute()
    yield process
    process.terminate()
    await process.wait()
    if process.failed:
        pytest.fail(f"Tunnel server process failed with exit code {process.returncode}")

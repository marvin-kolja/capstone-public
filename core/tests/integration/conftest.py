import pytest


@pytest.fixture(scope="module")
def tunnel_server_subprocess_port():
    # max user-defined port
    # https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml
    return 49151


@pytest.fixture(scope="module")
async def tunnel_server_subprocess(tunnel_server_subprocess_port):
    from core.subprocesses.tunnel_server_command import TunnelServerCommand
    from core.subprocesses.process import Process

    command = TunnelServerCommand(port=tunnel_server_subprocess_port)
    process = Process(command)
    await process.execute()
    yield process
    process.terminate()
    await process.wait()
    if process.failed:
        pytest.fail(f"Tunnel server process failed with exit code {process.returncode}")

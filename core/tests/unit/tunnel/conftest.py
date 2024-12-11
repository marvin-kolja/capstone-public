import asyncio

import pytest
from pymobiledevice3.remote.common import TunnelProtocol

from pymobiledevice3.remote.tunnel_service import TunnelResult as pymobiledevice3TunnelResult

from core.tunnel.tunnel_connect import TunnelResult


@pytest.fixture
def mocked_pymd3_tunnel_result(mocker):
    """
    A mocked `pymobiledevice3` TunnelResult` that can be used to simulate a tunnel result.
    """
    client = mocker.MagicMock()

    async def wait_closed():
        while not getattr(client, "closed", False):
            await asyncio.sleep(0.1)

    client.closed = False
    client.close = mocker.AsyncMock(side_effect=lambda: setattr(client, "closed", True))
    client.wait_closed = mocker.AsyncMock(side_effect=wait_closed)

    return pymobiledevice3TunnelResult(
        address="127.0.0.1",
        port=1234,
        protocol=TunnelProtocol.TCP,
        interface="",
        client=client
    )


@pytest.fixture
def fake_tunnel_result(mocked_pymd3_tunnel_result):
    """
    A fake tunnel result that can be used to simulate a tunnel result.
    """
    tunnel_result = TunnelResult(
        address=mocked_pymd3_tunnel_result.address,
        port=mocked_pymd3_tunnel_result.port,
        protocol=TunnelProtocol.TCP,
    )
    return tunnel_result


@pytest.fixture
async def mock_tunnel_connect__start_usbmux_tcp_tunnel_task(mocker, mocked_pymd3_tunnel_result):
    """
    A mock for the `_start_usbmux_tcp_tunnel_task` method that can be used to simulate a tunnel task.
    """

    async def start_tunnel_task(self, udid, queue):
        """
        Replaces the `pymobiledevice3` `TunneldCore.start_tunnel_task` method to simulate a tunnel task.

        It implements the most important parts of the methods to not break cleanup etc.

        Without this mock, the actual `TunneldCore.start_tunnel_task` method would try to connect to an actual device.
        """
        try:
            # This simulates a successful tunnel connection.
            self._tunnel_manager.tunnel_tasks[udid].tunnel = mocked_pymd3_tunnel_result
            self._tunnel_manager.tunnel_tasks[udid].udid = udid

            # Put the mocked tunnel result in the queue
            queue.put_nowait(mocked_pymd3_tunnel_result)

            # Simulate waiting for the tunnel to close.
            # Usually this would be very long-running, but for testing purposes we can just wait for a short time to not
            # break things if cleanup fails.
            await asyncio.sleep(1)
        finally:
            # We need to remove the tunnel task from the tunnel tasks to not break cleanup
            self._tunnel_manager.tunnel_tasks.pop(udid)

    def start_tcp_tunnel_using_usbmux(self, udid: str, queue: asyncio.Queue) -> asyncio.Task:
        task = asyncio.create_task(
            start_tunnel_task(self, udid, queue),
            name=f'start-tunnel-task-{udid}')
        return task

    mocker.patch("core.tunnel.tunnel_connect.TunnelConnect._start_usbmux_tcp_tunnel_task",
                 start_tcp_tunnel_using_usbmux)

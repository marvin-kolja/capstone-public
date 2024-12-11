import asyncio
from contextlib import suppress
from typing import Optional

from pydantic import BaseModel, IPvAnyAddress
from pymobiledevice3.exceptions import PyMobileDevice3Exception
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.common import TunnelProtocol
from pymobiledevice3.remote.tunnel_service import TunnelResult as pymobiledevice3TunnelResult, CoreDeviceTunnelProxy
from pymobiledevice3.tunneld import TunneldCore, TunnelTask

from core.exceptions.tunnel_connect import TunnelAlreadyExistsError


class TunnelResult(BaseModel):
    """
    A class to represent a tunnel connection result.
    """
    address: IPvAnyAddress
    port: int
    protocol: TunnelProtocol


class TunnelConnect:
    """
    A class to that wraps the TunneldCore functionality of `pymobiledevice`.

    The class is used to start, stop and get tunnels to devices.

    See method specific documentation for exact usage and connection types.
    """

    def __init__(self):
        self._tunnel_manager: TunneldCore = TunneldCore()

    def _start_usbmux_tcp_tunnel_task(self, udid: str, queue: asyncio.Queue) -> asyncio.Task:
        lockdown_client = create_using_usbmux(udid)
        service = CoreDeviceTunnelProxy(lockdown_client)
        task = asyncio.create_task(
            self._tunnel_manager.start_tunnel_task(udid, service, protocol=TunnelProtocol.TCP,
                                                   queue=queue),
            name=f'start-tunnel-task-{udid}')
        return task

    @staticmethod
    def _parse_pymobiledevice3_tunnel_result(tunnel_result: pymobiledevice3TunnelResult) -> TunnelResult:
        return TunnelResult(
            address=tunnel_result.address,
            port=tunnel_result.port,
            protocol=tunnel_result.protocol,
        )

    async def start_tunnel(self, udid: str) -> TunnelResult:
        """
        Start a tunnel to a device.

        For now only USBMux is supported using TCP.

        :param udid: The UDID of the device to connect to.

        :raises TunnelAlreadyExistsError: If a tunnel to the device already exists.
        """
        if self._tunnel_manager.tunnel_exists_for_udid(udid):
            raise TunnelAlreadyExistsError(f"Tunnel to {udid} already exists")

        queue = asyncio.Queue()

        try:
            task = self._start_usbmux_tcp_tunnel_task(udid, queue)
            self._tunnel_manager.tunnel_tasks[udid] = TunnelTask(task=task, udid=udid)

            tunnel: Optional[pymobiledevice3TunnelResult] = await queue.get()

            if tunnel is not None:
                return self._parse_pymobiledevice3_tunnel_result(tunnel)

            # If the tunnel is None, the task either failed or was cancelled.
            # Calling result() will re-raise the exception that caused the task to fail.
            #
            # If this raises an InvalidStateError and something is very wrong with the code.
            try:
                task.result()
            except asyncio.CancelledError:
                pass
        except PyMobileDevice3Exception as e:
            # TODO: Wrap PyMobileDevice3Exception in a custom exception
            raise e

    async def stop_tunnel(self, udid: str) -> None:
        """
        Stop the tunnel to a device.

        Does nothing if the tunnel does not exist.

        :param udid: The UDID of the device to disconnect from.
        """
        tunnel_task = self._tunnel_manager.tunnel_tasks.pop(udid, None)
        if tunnel_task is None:
            return
        if tunnel_task.tunnel is None or tunnel_task.udid is None:
            return
        if tunnel_task.task.done():
            return

        tunnel_task.task.cancel()

        # Suppress the CancelledError as it is expected.
        with suppress(asyncio.CancelledError):
            await tunnel_task.task

    def get_tunnel(self, udid: str) -> Optional[TunnelResult]:
        """
        Get the tunnel to a device.

        :param udid: The UDID of the device to get the tunnel for.
        :return: The tunnel result if the tunnel exists, otherwise None.
        """
        if self._tunnel_manager.tunnel_exists_for_udid(udid):
            tunnel_task = self._tunnel_manager.tunnel_tasks[udid]
            return self._parse_pymobiledevice3_tunnel_result(tunnel_task.tunnel)
        return None

    async def close(self):
        """
        Close all open tunnels.
        """
        tunnel_tasks = self._tunnel_manager.tunnel_tasks.copy()

        for udid in tunnel_tasks:
            tunnel_task = self._tunnel_manager.tunnel_tasks[udid]

            if tunnel_task is None:
                continue
            if tunnel_task.task.done():
                continue

            tunnel_task.task.cancel()

            # Suppress the CancelledError as it is expected.
            with suppress(asyncio.CancelledError):
                await tunnel_task.task
            # Trying to remove the task manually to not break cleanup.
            # The task should remove itself from the tunnel tasks on completion. However, it did occur that it may not.
            self._tunnel_manager.tunnel_tasks.pop(udid, None)

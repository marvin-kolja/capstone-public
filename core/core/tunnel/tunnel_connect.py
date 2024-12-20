import asyncio
import logging
from contextlib import suppress
from typing import Optional

from pymobiledevice3.exceptions import PyMobileDevice3Exception
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.common import TunnelProtocol
from pymobiledevice3.remote.tunnel_service import (
    TunnelResult as pymobiledevice3TunnelResult,
    CoreDeviceTunnelProxy,
)
from pymobiledevice3.tunneld import TunneldCore, TunnelTask

from core.exceptions.tunnel_connect import TunnelAlreadyExistsError
from core.tunnel.interface import TunnelConnectInterface, TunnelResult

logger = logging.getLogger(__name__)


class TunnelConnect(TunnelConnectInterface):
    """
    A class to that wraps the TunneldCore functionality of `pymobiledevice`.

    The class is used to start, stop and get tunnels to devices.

    See method specific documentation for exact usage and connection types.
    """

    def __init__(self):
        self._tunnel_manager: TunneldCore = TunneldCore()

    def _start_usbmux_tcp_tunnel_task(
        self, udid: str, queue: asyncio.Queue
    ) -> asyncio.Task:
        logger.debug(f"Starting tunnel task for device {udid}")
        lockdown_client = create_using_usbmux(udid)
        logger.debug(f"Created lockdown client for device {udid}")
        service = CoreDeviceTunnelProxy(lockdown_client)
        logger.debug(f"Created tunnel service for device {udid}")
        task = asyncio.create_task(
            self._tunnel_manager.start_tunnel_task(
                udid, service, protocol=TunnelProtocol.TCP, queue=queue
            ),
            name=f"start-tunnel-task-{udid}",
        )
        logger.debug(f"Created tunnel task for device {udid}")
        return task

    @staticmethod
    def _parse_pymobiledevice3_tunnel_result(
        tunnel_result: pymobiledevice3TunnelResult,
    ) -> TunnelResult:
        return TunnelResult(
            address=tunnel_result.address,
            port=tunnel_result.port,
            protocol=tunnel_result.protocol,
        )

    async def start_tunnel(self, udid: str) -> TunnelResult:
        if self._tunnel_manager.tunnel_exists_for_udid(udid):
            logger.warning(f"Tunnel to device {udid} already exists")
            raise TunnelAlreadyExistsError()

        queue = asyncio.Queue()

        try:
            task = self._start_usbmux_tcp_tunnel_task(udid, queue)

            self._tunnel_manager.tunnel_tasks[udid] = TunnelTask(task=task, udid=udid)

            tunnel: Optional[pymobiledevice3TunnelResult] = await queue.get()
            logger.debug(f"Got tunnel result for device {udid}: {tunnel}")

            if tunnel is not None:
                logger.info(f"Started tunnel for device {udid}")
                return self._parse_pymobiledevice3_tunnel_result(tunnel)

            try:
                # If the tunnel is None, the task either failed or was cancelled.
                # Calling result() will re-raise the exception that caused the task to fail.
                task.result()
            except asyncio.CancelledError:
                logger.debug(f"Tunnel task for device {udid} was cancelled")
                pass
            except asyncio.InvalidStateError as e:
                logger.critical(
                    f"Tunnel task result is not available. This should not happen. {e}",
                    exc_info=True,
                )
                raise e
        except PyMobileDevice3Exception as e:
            logger.error(
                f"Failed with pymobiledevice3 exception to start tunnel for device {udid}: {e}",
                exc_info=True,
            )
            # TODO: Wrap PyMobileDevice3Exception in a custom exception
            raise e

    async def stop_tunnel(self, udid: str) -> None:
        tunnel_task = self._tunnel_manager.tunnel_tasks.pop(udid, None)
        if tunnel_task is None:
            logger.debug(f"Tunnel task for device {udid} does not exist")
            return
        if tunnel_task.tunnel is None or tunnel_task.udid is None:
            logger.debug(f"Tunnel task for device {udid} is missing required data")
            return
        if tunnel_task.task.done():
            logger.debug(f"Tunnel task for device {udid} is already done")
            return

        logger.debug(f"Cancelling tunnel task for device {udid}")
        tunnel_task.task.cancel()

        # Suppress the CancelledError as it is expected.
        with suppress(asyncio.CancelledError):
            logger.debug(f"Waiting for tunnel task for device {udid} to finish")
            await tunnel_task.task
            logger.debug(f"Tunnel task for device {udid} finished")

    def get_tunnel(self, udid: str) -> Optional[TunnelResult]:
        if self._tunnel_manager.tunnel_exists_for_udid(udid):
            tunnel_task = self._tunnel_manager.tunnel_tasks[udid]
            logger.debug(f"Got tunnel for device {udid}")
            return self._parse_pymobiledevice3_tunnel_result(tunnel_task.tunnel)
        logger.debug(f"Tunnel for device {udid} does not exist")
        return None

    async def close(self):
        """
        Close all open tunnels.
        """
        logger.debug("Closing all open tunnels")

        tunnel_tasks = self._tunnel_manager.tunnel_tasks.copy()

        for udid in tunnel_tasks:
            tunnel_task = self._tunnel_manager.tunnel_tasks[udid]

            if tunnel_task is None:
                logger.debug(f"Tunnel task for device {udid} does not exist")
                continue
            if tunnel_task.task.done():
                logger.debug(f"Tunnel task for device {udid} is already done")
                continue

            logger.debug(f"Cancelling tunnel task for device {udid}")
            tunnel_task.task.cancel()

            # Suppress the CancelledError as it is expected.
            with suppress(asyncio.CancelledError):
                logger.debug(f"Waiting for tunnel task for device {udid} to finish")
                await tunnel_task.task
                logger.debug(f"Tunnel task for device {udid} finished")
            # Trying to remove the task manually to not break cleanup.
            # The task should remove itself from the tunnel tasks on completion. However, it did occur that it may not.
            if udid in self._tunnel_manager.tunnel_tasks:
                logger.warning(
                    f"Tunnel task for device {udid} did not remove itself from the tunnel tasks, removing manually"
                )
                self._tunnel_manager.tunnel_tasks.pop(udid, None)

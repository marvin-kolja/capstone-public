import asyncio
from typing import Optional

from pydantic import BaseModel, IPvAnyAddress
from pymobiledevice3.remote.common import TunnelProtocol
from pymobiledevice3.remote.tunnel_service import TunnelResult as pymobiledevice3TunnelResult
from pymobiledevice3.tunneld import TunneldCore


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
        raise NotImplementedError()

    @staticmethod
    def _parse_pymobiledevice3_tunnel_result(tunnel_result: pymobiledevice3TunnelResult) -> TunnelResult:
        raise NotImplementedError()

    async def start_tunnel(self, udid: str) -> TunnelResult:
        """
        Start a tunnel to a device.

        For now only USBMux is supported using TCP.

        :param udid: The UDID of the device to connect to.

        :raises TunnelAlreadyExistsError: If a tunnel to the device already exists.
        """
        # TODO: use `self._start_usbmux_tcp_tunnel_task` to start the tunnel
        # TODO: use `self._parse_pymobiledevice3_tunnel_result` to parse the tunnel result to our model
        raise NotImplementedError()

    async def stop_tunnel(self, udid: str) -> None:
        """
        Stop the tunnel to a device.

        Does nothing if the tunnel does not exist.

        :param udid: The UDID of the device to disconnect from.
        """
        raise NotImplementedError()

    def get_tunnel(self, udid: str) -> Optional[TunnelResult]:
        """
        Get the tunnel to a device.

        :param udid: The UDID of the device to get the tunnel for.
        :return: The tunnel result if the tunnel exists, otherwise None.
        """
        raise NotImplementedError()

    async def close(self):
        """
        Close all open tunnels.
        """
        raise NotImplementedError()

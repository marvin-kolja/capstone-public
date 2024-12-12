from asyncio import Protocol

from pydantic import BaseModel, IPvAnyAddress
from pymobiledevice3.remote.common import TunnelProtocol


class TunnelResult(BaseModel):
    """
    A class to represent a tunnel connection result.
    """
    address: IPvAnyAddress
    port: int
    protocol: TunnelProtocol


class TunnelConnectInterface(Protocol):
    async def start_tunnel(self, udid: str) -> TunnelResult:
        """
        Start a tunnel to a device.

        For now only USBMux is supported using TCP.

        :param udid: The UDID of the device to connect to.
        :return: The tunnel result.

        :raises TunnelAlreadyExistsError: If a tunnel to the device already exists.
        :raises DeviceNotFoundError: If the device with the UDID is not found.
        :raises NoDeviceConnectedError: If no device is connected.
        """
        ...

    async def stop_tunnel(self, udid: str) -> None:
        """
        Stop the tunnel to a device.

        Does nothing if the tunnel does not exist.

        :param udid: The UDID of the device to disconnect from.
        """
        ...

    async def get_tunnel(self, udid: str) -> TunnelResult:
        """
        Get the tunnel to a device.

        :param udid: The UDID of the device to get the tunnel for.
        :return: The tunnel result if the tunnel exists, otherwise None.
        """
        ...

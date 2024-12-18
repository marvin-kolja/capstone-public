from pymobiledevice3 import lockdown, usbmux, exceptions
from pymobiledevice3.lockdown import LockdownClient

from core.device.i_device import IDevice


class IDeviceManager:
    def __init__(self):
        self.__devices: dict[str, IDevice] = {}

    def _browse_lockdown_clients(self) -> list[LockdownClient]:
        """
        Handles logic for browsing available devices as lockdown clients.
        """
        raise NotImplementedError()

    def list_devices(self) -> list[IDevice]:
        """
        Get a list of all available devices as IDevice instances.

        Discovered devices are stored in memory and refreshed when this method is called again.
        """
        lockdown_clients = self._browse_lockdown_clients()
        raise NotImplementedError

    def get_device(self, udid: str) -> IDevice:
        """
        Get a device by its UDID using usbmux

        This is a convenience method for calling `list_devices()` and searching if the udid is in the list.
        """
        raise NotImplementedError

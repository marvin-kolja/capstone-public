from pymobiledevice3 import lockdown, usbmux
from pymobiledevice3.lockdown import UsbmuxLockdownClient

from core.device.i_device import IDevice


class IDeviceManager:
    def __init__(self):
        self.__devices: dict[str, IDevice] = {}

    @staticmethod
    def _browse_lockdown_clients() -> list[UsbmuxLockdownClient]:
        """
        Handles logic for browsing available devices as lockdown clients.
        """
        mux_devices = usbmux.list_devices(usbmux_address=None)
        return [lockdown.create_using_usbmux(mux_device.serial, autopair=False) for mux_device in mux_devices]

    def list_devices(self) -> list[IDevice]:
        """
        Get a list of all available devices as IDevice instances.

        Discovered devices are stored in memory and refreshed when this method is called again.
        """
        lockdown_clients = self._browse_lockdown_clients()

        for lockdown_client in lockdown_clients:
            udid = lockdown_client.udid

            if udid in self.__devices:
                continue

            self.__devices[udid] = IDevice(lockdown_client=lockdown_client)

        return list(self.__devices.values())

    def get_device(self, udid: str) -> IDevice:
        """
        Get a device by its UDID using usbmux

        This is a convenience method for calling `list_devices()` and searching if the udid is in the list.
        """
        raise NotImplementedError

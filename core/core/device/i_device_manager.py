from pymobiledevice3 import lockdown, usbmux, exceptions

from core.device.i_device import IDevice


class IDeviceManager:
    def __init__(self):
        self.__devices: dict[str, IDevice] = {}

    def list_devices(self) -> list[IDevice]:
        """
        List all devices found using usbmux

        Found devices are stored in memory and refreshed when this method is called again.
        """
        raise NotImplementedError

    def get_device(self, udid: str) -> IDevice:
        """
        Get a device by its UDID using usbmux

        This is a convenience method for calling `list_devices()` and searching if the udid is in the list.
        """
        raise NotImplementedError

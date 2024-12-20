import logging
from typing import Optional

from pymobiledevice3 import lockdown, usbmux
from pymobiledevice3.lockdown import UsbmuxLockdownClient

from core.device.i_device import IDevice

logger = logging.getLogger(__name__)


class IDeviceManager:
    def __init__(self):
        self.__devices: dict[str, IDevice] = {}

    @staticmethod
    def _browse_lockdown_clients() -> list[UsbmuxLockdownClient]:
        """
        Handles logic for browsing available devices as lockdown clients.
        """
        logger.debug("Browsing for Usbmux devices")
        mux_devices = usbmux.list_devices(usbmux_address=None)
        logger.debug(f"Found {len(mux_devices)} Usbmux devices")
        lockdown_clients = [
            lockdown.create_using_usbmux(mux_device.serial, autopair=False)
            for mux_device in mux_devices
        ]
        logger.debug(f"Created {len(lockdown_clients)} lockdown clients")
        return lockdown_clients

    def list_devices(self) -> list[IDevice]:
        """
        Get a list of all available devices as IDevice instances.

        Discovered devices are stored in memory and refreshed when this method is called again.
        """
        lockdown_clients = self._browse_lockdown_clients()

        # Remove devices that are no longer discovered during browse
        new_udid_list = [client.udid for client in lockdown_clients]
        existing_udid_list = [udid for udid in self.__devices.keys()]
        for udid in existing_udid_list:
            logger.debug(
                f"Checking if IDevice with {udid} is stale and requires removal"
            )
            if udid not in new_udid_list:
                logger.debug(f"Removing {udid} from devices list")
                del self.__devices[udid]

        for lockdown_client in lockdown_clients:
            udid = lockdown_client.udid

            if udid in self.__devices:
                logger.debug(f"IDevice with {udid} is already stored in devices list")
                continue

            self.__devices[udid] = IDevice(lockdown_client=lockdown_client)
            logger.debug(f"Created IDevice with {udid} and stored it in devices list")

        return list(self.__devices.values())

    def get_device(self, udid: str) -> Optional[IDevice]:
        """
        Get a device by its UDID using usbmux

        This is a convenience method for calling `list_devices()` and searching if the udid is stored
        """
        devices = self.list_devices()
        for device in devices:
            if device.lockdown_client.udid == udid:
                logger.debug(f"Found IDevice with {udid} in devices list")
                return device

        logger.debug(f"No IDevice in devices list matching {udid}")
        return None

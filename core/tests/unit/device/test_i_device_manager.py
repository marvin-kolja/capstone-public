from unittest.mock import patch, MagicMock

import pytest
from pymobiledevice3.lockdown import UsbmuxLockdownClient

from core.device.i_device import IDevice
from core.device.i_device_manager import IDeviceManager


@pytest.fixture
def device_manager():
    return IDeviceManager()


@pytest.mark.parametrize("paired,developer_mode_enabled,product_version", [(True, True, "18.0")])
class TestIDeviceManager:

    def test_list_devices(self, device_manager, mock_usbmux_lockdown_client):
        """
        GIVEN: An `IDeviceManager` instance

        WHEN: Listing all available devices

        THEN: Should return a list of `IDevice`
        """
        with patch.object(device_manager, '_browse_lockdown_clients', return_value=[mock_usbmux_lockdown_client]):
            devices = device_manager.list_devices()
            assert len(devices) > 0
            assert isinstance(devices[0], IDevice)
            assert devices[0].lockdown_client is mock_usbmux_lockdown_client

    def test_list_devices_delete_stale_devices(self, device_manager, mock_usbmux_lockdown_client):
        """
        GIVEN: An `IDeviceManager` instance
        AND: An existing `IDevice` stored in `device_manager`

        WHEN: Listing all available devices
        AND: The udid isn't discovered anymore.

        THEN: The `IDevice` should be deleted from the `device_manager`
        """
        device_manager._IDeviceManager__devices = {
            mock_usbmux_lockdown_client.udid: mock_usbmux_lockdown_client,
        }

        with patch.object(device_manager, '_browse_lockdown_clients', return_value=[]):
            # Simulate that devices is no longer found.

            devices = device_manager.list_devices()
            assert len(devices) == 0
            assert device_manager._IDeviceManager__devices is {}

    def test_list_devices_skip_storing_existing_devices(self, device_manager, mock_usbmux_lockdown_client):
        """
        GIVEN: An `IDeviceManager` instance
        AND: An existing `IDevice` stored in `device_manager`

        WHEN: Listing all available devices
        AND: The udid is discovered again.

        THEN: The `IDevice` should not replace the existing `IDevice` or add a new one.
        """
        udid = mock_usbmux_lockdown_client.udid

        device_manager._IDeviceManager__devices = {
            udid: mock_usbmux_lockdown_client,
        }

        another_mocked_lockdown_client = mock_usbmux_lockdown_client
        another_mocked_lockdown_client.udid = udid

        with patch.object(device_manager, '_browse_lockdown_clients', return_value=[another_mocked_lockdown_client]):
            devices = device_manager.list_devices()
            assert len(devices) == 1
            assert device_manager._IDeviceManager__devices[udid] == mock_usbmux_lockdown_client

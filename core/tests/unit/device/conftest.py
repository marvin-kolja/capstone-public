from unittest.mock import MagicMock, PropertyMock

import pytest
from pymobiledevice3 import exceptions as pmd3_exceptions
from pymobiledevice3.lockdown import UsbmuxLockdownClient

from core.device.i_device import IDevice


@pytest.fixture()
def mock_usbmux_lockdown_client(paired, developer_mode_enabled, product_version, fake_udid) -> UsbmuxLockdownClient:
    mock_instance = MagicMock(spec=UsbmuxLockdownClient)
    mock_instance.product_version = product_version
    mock_instance.paired = paired
    if not paired:
        type(mock_instance).developer_mode_status = PropertyMock(side_effect=pmd3_exceptions.NotPairedError())
    else:
        mock_instance.developer_mode_status = developer_mode_enabled
    mock_instance.udid = fake_udid
    return mock_instance


@pytest.fixture()
def i_device(mock_usbmux_lockdown_client):
    return IDevice(lockdown_client=mock_usbmux_lockdown_client)

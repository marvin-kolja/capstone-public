from unittest.mock import MagicMock

import pytest
from core.device.i_device import IDevice, IDeviceInfo, IDeviceStatus
from core.device.i_device_manager import IDeviceManager


@pytest.fixture
def mock_i_device(random_device_id):
    device_mock = MagicMock(spec=IDevice)
    device_mock.udid = random_device_id
    device_mock.info = IDeviceInfo(
        device_name="DeviceName",
        device_class="iPhone",
        build_version="22B91",
        product_type="iPhone14,4",
        product_version="18.1.1",
    )
    device_mock.status = IDeviceStatus(
        paired=True,
        developer_mode_enabled=True,
        ddi_mounted=True,
        tunnel_connected=True,
    )

    return device_mock


@pytest.fixture
def mock_device_manager(mock_i_device):
    device_manager_mock = MagicMock(spec=IDeviceManager)
    return device_manager_mock

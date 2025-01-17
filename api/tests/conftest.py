import random
import string
from typing import Generator
from unittest.mock import MagicMock

import pytest
from core.device.i_device import IDevice, IDeviceInfo, IDeviceStatus
from core.device.i_device_manager import IDeviceManager
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.models import DeviceWithStatus, DeviceBase


def assert_base_device_equal(device: DeviceBase, expected_device: DeviceBase):
    assert DeviceBase.model_validate(device) == DeviceBase.model_validate(
        expected_device
    )


def assert_base_device_equal_to_idevice(device: DeviceBase, idevice: IDevice):
    assert_base_device_equal(
        device,
        DeviceWithStatus.model_validate(
            {
                "id": idevice.udid,
                "udid": idevice.udid,
                **idevice.info.model_dump(),
                "connected": True,
                "status": idevice.status,
            },
        ),
    )


@pytest.fixture
def random_device_id():
    """
    Generate a random device ID like "00000000-0000000000000000"
    """
    return (
        "".join(random.choices(string.digits, k=8))
        + "-"
        + "".join(random.choices(string.digits + string.ascii_uppercase, k=16))
    )


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


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as c:
        yield c


@pytest.fixture(scope="module")
async def async_client() -> Generator[AsyncClient, None, None]:
    async with AsyncClient(
        transport=ASGITransport(
            app=app,
            raise_app_exceptions=False,
        ),
        base_url="http://test",
    ) as ac:
        yield ac

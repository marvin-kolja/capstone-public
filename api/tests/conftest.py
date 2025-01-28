import random
import string
from typing import Generator
from unittest.mock import MagicMock

import pytest
from core.device.i_device import IDevice, IDeviceInfo, IDeviceStatus
from core.device.i_device_manager import IDeviceManager
from core.xc.xcresult.models.test_results.summary import Summary
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
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(
            app=app,
            raise_app_exceptions=False,
        ),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
def test_summary():
    """
    Return a test summary object.

    This is a real test summary object from a Xcode test run.
    """

    return Summary.model_validate(
        {
            "devicesAndConfigurations": [
                {
                    "device": {
                        "architecture": "arm64e",
                        "deviceId": "00000000-0000000000000000",
                        "deviceName": "iPhone",
                        "modelName": "iPhone SE",
                        "osVersion": "17.5.1",
                        "platform": "iOS",
                    },
                    "expectedFailures": 0,
                    "failedTests": 0,
                    "passedTests": 1,
                    "skippedTests": 0,
                    "testPlanConfiguration": {
                        "configurationId": "1",
                        "configurationName": "Test Scheme Action",
                    },
                }
            ],
            "environmentDescription": "RP Swift · Built with macOS 15.1.1",
            "expectedFailures": 0,
            "failedTests": 0,
            "finishTime": 1737456113.034,
            "passedTests": 1,
            "result": "Passed",
            "skippedTests": 0,
            "startTime": 1737456094.16,
            "statistics": [],
            "testFailures": [],
            "title": "Test - RP Swift",
            "topInsights": [],
            "totalTestCount": 1,
        }
    )

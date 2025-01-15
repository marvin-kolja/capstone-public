from core.device.i_device import IDevice

from api.api_models import DeviceWithStatus
from api.db_models import DeviceBase


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

import pytest

from api.models import DeviceWithStatus, DeviceBase, Device

# noinspection PyProtectedMember
from api.services.device_service import (
    _update_device_fields,
    _update_or_add,
)
from tests.conftest import assert_base_device_equal


@pytest.mark.asyncio
async def test_update_device_fields():
    """
    GIVEN: a device from DB
    AND: a new device base

    WHEN: calling `_update_device_fields` with the device and the new device base

    THEN: all fields of the device should be updated
    AND: the same device object should be returned
    """
    device = Device.model_validate(
        {
            "id": "udid",
            "udid": "udid",
            "device_name": "device_name",
            "device_class": "device_class",
            "build_version": "build_version",
            "product_version": "product_version",
            "product_type": "product_type",
        }
    )
    new_device = DeviceBase.model_validate(
        {
            "device_name": "new_device_name",
            "device_class": "new_device_class",
            "build_version": "new_build_version",
            "product_version": "new_product_version",
            "product_type": "new_product_type",
        }
    )

    updated_device = _update_device_fields(device, new_device)

    assert updated_device is device  # should return the same object not a new one

    assert updated_device.id == device.id
    assert updated_device.udid == device.udid

    assert_base_device_equal(updated_device, new_device)


@pytest.mark.parametrize(
    "device_from_db",
    [
        None,
        Device.model_validate(
            {
                "id": "udid",
                "udid": "udid",
                "device_name": "device_name",
                "device_class": "device_class",
                "build_version": "build_version",
                "product_version": "product_version",
                "product_type": "product_type",
            }
        ),
    ],
)
@pytest.mark.asyncio
async def test_update_or_add(device_from_db):
    """
    GIVEN: a device with status
    AND: an optional device from db

    WHEN: calling `_update_or_add` with the device with status and the optional device from db

    THEN: if the device from db exists, it should be updated, otherwise a new device should be created
    """
    device_with_status = DeviceWithStatus.model_validate(
        {
            "id": "udid",
            "udid": "udid",
            "device_name": "device_name",
            "device_class": "device_class",
            "build_version": "build_version",
            "product_version": "product_version",
            "product_type": "product_type",
            "connected": True,
            "status": {
                "paired": False,
                "developer_mode_enabled": False,
                "ddi_mounted": False,
                "tunnel_connected": False,
            },
        }
    )
    updated_device = _update_or_add(device_with_status, device_from_db)

    if device_from_db:
        assert updated_device is device_from_db
    else:
        assert isinstance(updated_device, Device)
        assert updated_device.id == device_with_status.id
        assert updated_device.udid == device_with_status.udid
        assert_base_device_equal(updated_device, device_with_status)

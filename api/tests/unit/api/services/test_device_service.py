from unittest.mock import MagicMock, patch

import pytest
from core.device.i_device import IDevice
from core.device.i_device_manager import IDeviceManager
from core.exceptions import i_device as core_device_exceptions
from fastapi import HTTPException

from api.models import DeviceWithStatus, DeviceBase, Device

# noinspection PyProtectedMember
from api.services.device_service import (
    _update_device_fields,
    _update_or_add,
    _get_connected_device_or_raise,
    pair_device,
    enable_developer_mode,
    unpair_device,
    mount_ddi,
    unmount_ddi,
    connect_tunnel,
)
from tests.conftest import assert_base_device_equal


def test_update_device_fields():
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
def test_update_or_add(device_from_db):
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


@pytest.mark.parametrize(
    "device_exists",
    [
        True,
        False,
    ],
)
def test_get_connected_device_or_raise(mock_device_manager, device_exists):
    """
    GIVEN: a device id

    WHEN: calling `_get_connected_device_or_raise` with the device id

    THEN: if the device exists, it should be returned, otherwise a 404 error should be raised
    """
    i_device_mock = MagicMock(spec=IDevice)
    mock_device_manager.get_device.return_value = (
        i_device_mock if device_exists else None
    )

    if device_exists:
        assert (
            _get_connected_device_or_raise("device_id", mock_device_manager)
            == i_device_mock
        )
    else:
        with pytest.raises(HTTPException) as e:
            _get_connected_device_or_raise("device_id", mock_device_manager)

        assert e.value.status_code == 404
        assert e.value.detail == "Device not found"


@pytest.mark.parametrize(
    "exception_raised",
    [
        core_device_exceptions.UserDeniedPairing,
        core_device_exceptions.PasswordRequired,
    ],
)
def test_pair_device_exception(exception_raised, random_device_id):
    """
    GIVEN: A device that raises an exception when pairing

    WHEN: Calling `pair_device`
    AND: The underlying method raises an exception

    THEN: A HTTPException 400 should be raised
    """
    with patch(
        "api.services.device_service._get_connected_device_or_raise"
    ) as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.pair.side_effect = exception_raised

        with pytest.raises(HTTPException) as e:
            pair_device(
                device_id=random_device_id,
                device_manager=MagicMock(spec=IDeviceManager),
            )

        assert e.value.status_code == 400


@pytest.mark.parametrize(
    "exception_raised",
    [
        core_device_exceptions.DeviceNotPaired,
    ],
)
def test_unpair_device_exception(exception_raised, random_device_id):
    """
    GIVEN: A device that raises an exception when unpairing

    WHEN: Calling `unpair_device`
    AND: The underlying method raises an exception

    THEN: A HTTPException 400 should be raised
    """
    with patch(
        "api.services.device_service._get_connected_device_or_raise"
    ) as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.unpair.side_effect = exception_raised

        with pytest.raises(HTTPException) as e:
            unpair_device(
                device_id=random_device_id,
                device_manager=MagicMock(spec=IDeviceManager),
            )

        assert e.value.status_code == 400


@pytest.mark.parametrize(
    "exception_raised",
    [
        core_device_exceptions.DeveloperModeNotSupported,
        core_device_exceptions.DeveloperModeAlreadyEnabled,
        core_device_exceptions.DeviceHasPasscodeSet,
        core_device_exceptions.DeviceNotPaired,
    ],
)
def test_enable_developer_mode(exception_raised, random_device_id):
    """
    GIVEN: A device that raises an exception when enabling developer mode

    WHEN: Calling `enable_developer_mode`
    AND: The underlying method raises an exception

    THEN: A HTTPException 400 should be raised
    """
    with patch(
        "api.services.device_service._get_connected_device_or_raise"
    ) as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.enable_developer_mode.side_effect = exception_raised

        with pytest.raises(HTTPException) as e:
            enable_developer_mode(
                device_id=random_device_id,
                device_manager=MagicMock(spec=IDeviceManager),
            )

        assert e.value.status_code == 400


@pytest.mark.parametrize(
    "exception_raised",
    [
        core_device_exceptions.DdiAlreadyMounted,
        core_device_exceptions.DeveloperModeNotEnabled,
        core_device_exceptions.DeveloperModeError,
        core_device_exceptions.DeviceNotPaired,
    ],
)
@pytest.mark.asyncio
async def test_mount_ddi(exception_raised, random_device_id):
    """
    GIVEN: A device that raises an exception when mounting DDI

    WHEN: Calling `mount_ddi`
    AND: The underlying method raises an exception

    THEN: A HTTPException 400 should be raised
    """
    with patch(
        "api.services.device_service._get_connected_device_or_raise"
    ) as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.mount_ddi.side_effect = exception_raised

        with pytest.raises(HTTPException) as e:
            await mount_ddi(
                device_id=random_device_id,
                device_manager=MagicMock(spec=IDeviceManager),
            )

        assert e.value.status_code == 400


@pytest.mark.parametrize(
    "exception_raised",
    [
        core_device_exceptions.DdiNotMounted,
        core_device_exceptions.DeveloperModeNotEnabled,
        core_device_exceptions.DeveloperModeError,
        core_device_exceptions.DeviceNotPaired,
    ],
)
@pytest.mark.asyncio
async def test_unmount_ddi(exception_raised, random_device_id):
    """
    GIVEN: A device that raises an exception when unmounting DDI

    WHEN: Calling `unmount_ddi`
    AND: The underlying method raises an exception

    THEN: A HTTPException 400 should be raised
    """
    with patch(
        "api.services.device_service._get_connected_device_or_raise"
    ) as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.unmount_ddi.side_effect = exception_raised

        with pytest.raises(HTTPException) as e:
            await unmount_ddi(
                device_id=random_device_id,
                device_manager=MagicMock(spec=IDeviceManager),
            )

        assert e.value.status_code == 400


@pytest.mark.parametrize(
    "exception_raised",
    [
        core_device_exceptions.DeviceNotPaired,
        core_device_exceptions.DeveloperModeNotEnabled,
        core_device_exceptions.DdiNotMounted,
        core_device_exceptions.RsdNotSupported,
    ],
)
@pytest.mark.asyncio
async def test_connect_tunnel(exception_raised, random_device_id):
    """
    GIVEN: A device that raises an exception when connecting tunnel

    WHEN: Calling `connect_tunnel`
    AND: The underlying method raises an exception

    THEN: A HTTPException 400 should be raised
    """
    with patch(
        "api.services.device_service._get_connected_device_or_raise"
    ) as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.establish_trusted_channel.side_effect = exception_raised

        with pytest.raises(HTTPException) as e:
            await connect_tunnel(
                device_id=random_device_id,
                device_manager=MagicMock(spec=IDeviceManager),
            )

        assert e.value.status_code == 400

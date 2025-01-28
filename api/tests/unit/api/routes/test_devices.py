from unittest.mock import MagicMock, patch

import pytest
from core.device.i_device import IDevice
from core.exceptions import i_device as core_device_exceptions
from fastapi import HTTPException

# noinspection PyProtectedMember
from api.routes.devices import _get_i_device_or_raise


@pytest.mark.parametrize(
    "exception_raised, status_code",
    [
        (core_device_exceptions.UserDeniedPairing, 400),
        (core_device_exceptions.PasswordRequired, 400),
    ],
)
@pytest.mark.asyncio
async def test_pair_device_exception(
    exception_raised, random_device_id, async_client, status_code
):
    """
    GIVEN: A device that raises an exception when pairing

    WHEN: POSTing to the `/devices/{device_id}/pair` endpoint
    AND: The underlying method raises an exception

    THEN: The response status code should match the expected status code
    """
    with patch("api.routes.devices._get_i_device_or_raise") as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.pair.side_effect = exception_raised

        r = await async_client.post(f"/devices/{random_device_id}/pair")

        assert r.status_code == status_code
        mock_get_device.assert_called_once()


@pytest.mark.parametrize(
    "exception_raised, status_code",
    [
        (core_device_exceptions.DeviceNotPaired, 400),
    ],
)
@pytest.mark.asyncio
async def test_unpair_device_exception(
    exception_raised, random_device_id, async_client, status_code
):
    """
    GIVEN: A device that raises an exception when unpairing

    WHEN: POSTing to the `/devices/{device_id}/unpair` endpoint
    AND: The underlying method raises an exception

    THEN: The response status code should match the expected status code
    """
    with patch("api.routes.devices._get_i_device_or_raise") as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.unpair.side_effect = exception_raised

        r = await async_client.post(f"/devices/{random_device_id}/unpair")

        assert r.status_code == status_code
        mock_get_device.assert_called_once()


@pytest.mark.parametrize(
    "exception_raised, status_code",
    [
        (core_device_exceptions.DeveloperModeNotSupported, 400),
        (core_device_exceptions.DeveloperModeAlreadyEnabled, 400),
        (core_device_exceptions.DeviceHasPasscodeSet, 400),
        (core_device_exceptions.DeviceNotPaired, 400),
    ],
)
@pytest.mark.asyncio
async def test_enable_developer_mode(
    exception_raised, random_device_id, async_client, status_code
):
    """
    GIVEN: A device that raises an exception when enabling developer mode

    WHEN: POSTing to the `/devices/{device_id}/developer-mode/enable` endpoint
    AND: The underlying method raises an exception

    THEN: The response status code should match the expected status code
    """
    with patch("api.routes.devices._get_i_device_or_raise") as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.enable_developer_mode.side_effect = exception_raised

        r = await async_client.post(
            f"/devices/{random_device_id}/developer-mode/enable"
        )

        assert r.status_code == status_code
        mock_get_device.assert_called_once()


@pytest.mark.parametrize(
    "exception_raised, status_code",
    [
        (core_device_exceptions.DdiAlreadyMounted, 400),
        (core_device_exceptions.DdiMountingError, 500),
        (core_device_exceptions.DeveloperModeNotEnabled, 400),
        (core_device_exceptions.DeviceNotPaired, 400),
    ],
)
@pytest.mark.asyncio
async def test_mount_ddi(exception_raised, random_device_id, async_client, status_code):
    """
    GIVEN: A device that raises an exception when mounting DDI

    WHEN: POSTing to the `/devices/{device_id}/ddi/mount` endpoint
    AND: The underlying method raises an exception

    THEN: The response status code should match the expected status code
    """
    with patch("api.routes.devices._get_i_device_or_raise") as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.mount_ddi.side_effect = exception_raised

        r = await async_client.post(f"/devices/{random_device_id}/ddi/mount")

        assert r.status_code == status_code
        mock_get_device.assert_called_once()


@pytest.mark.parametrize(
    "exception_raised, status_code",
    [
        (core_device_exceptions.DdiNotMounted, 400),
        (core_device_exceptions.DdiMountingError, 500),
        (core_device_exceptions.DeveloperModeNotEnabled, 400),
        (core_device_exceptions.DeviceNotPaired, 400),
    ],
)
@pytest.mark.asyncio
async def test_unmount_ddi(
    exception_raised, random_device_id, async_client, status_code
):
    """
    GIVEN: A device that raises an exception when unmounting DDI

    WHEN: POSTing to the `/devices/{device_id}/ddi/unmount` endpoint
    AND: The underlying method raises an exception

    THEN: The response status code should match the expected status code
    """
    with patch("api.routes.devices._get_i_device_or_raise") as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.unmount_ddi.side_effect = exception_raised

        r = await async_client.post(f"/devices/{random_device_id}/ddi/unmount")

        assert r.status_code == status_code
        mock_get_device.assert_called_once()


@pytest.mark.parametrize(
    "exception_raised, status_code",
    [
        (core_device_exceptions.DeviceNotPaired, 400),
        (core_device_exceptions.DeveloperModeNotEnabled, 400),
        (core_device_exceptions.DdiNotMounted, 400),
        (core_device_exceptions.RsdNotSupported, 400),
    ],
)
@pytest.mark.asyncio
async def test_connect_tunnel(
    exception_raised, random_device_id, async_client, status_code
):
    """
    GIVEN: A device that raises an exception when connecting tunnel

    WHEN: POSTing to the `/devices/{device_id}/tunnel/connect` endpoint
    AND: The underlying method raises an exception

    THEN: The response status code should match the expected status code
    """
    with patch("api.routes.devices._get_i_device_or_raise") as mock_get_device:
        device_mock = MagicMock(spec=IDevice)
        mock_get_device.return_value = device_mock
        device_mock.establish_trusted_channel.side_effect = exception_raised

        r = await async_client.post(f"/devices/{random_device_id}/tunnel/connect")

        assert r.status_code == status_code
        mock_get_device.assert_called_once()


@pytest.mark.parametrize(
    "device_exists",
    [
        True,
        False,
    ],
)
@pytest.mark.asyncio
async def test_get_i_device_or_raise(mock_device_manager, device_exists):
    """
    GIVEN: a device id

    WHEN: calling `_get_i_device_or_raise` with the device id

    THEN: if the device exists, it should be returned, otherwise a 404 error should be raised
    """
    i_device_mock = MagicMock(spec=IDevice)
    mock_device_manager.get_device.return_value = (
        i_device_mock if device_exists else None
    )

    if device_exists:
        assert _get_i_device_or_raise("device_id", mock_device_manager) == i_device_mock
    else:
        with pytest.raises(HTTPException) as e:
            await _get_i_device_or_raise("device_id", mock_device_manager)

        assert e.value.status_code == 404
        assert e.value.detail == "Device is not connected"

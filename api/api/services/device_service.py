import logging
from typing import Optional

from core.device.i_device_manager import IDeviceManager
from core.exceptions import i_device as core_device_exceptions
from fastapi import HTTPException
from sqlmodel import Session, select, col

from api.api_models import DeviceWithStatus
from api.db_models import Device, DeviceBase
from api.services.helpers import update_db_model

logger = logging.getLogger(__name__)


def list_devices(
    *, session: Session, device_manager: IDeviceManager
) -> list[DeviceWithStatus]:
    devices = device_manager.list_devices()

    logger.debug(f"Found {len(devices)} devices")

    devices_to_return: list[DeviceWithStatus] = []

    for device in devices:
        device_with_status = DeviceWithStatus(
            id=device.udid,
            udid=device.udid,
            **device.info.model_dump(),
            connected=True,
            status=device.status,
        )
        devices_to_return.append(device_with_status)
        device_from_db = session.get(Device, device.udid)
        session.add(_update_or_add(device_with_status, device_from_db))

    session.commit()

    connected_device_ids = [d.id for d in devices_to_return]

    logger.debug(
        f"Trying to get devices from DB that are not connected: {connected_device_ids}"
    )

    statement = select(Device).where(col(Device.id).notin_(connected_device_ids))
    devices_from_db = session.exec(statement).all()

    logger.debug(f"Found {len(devices_from_db)} devices from DB that are not connected")

    devices_to_return.extend(
        [DeviceWithStatus.model_validate(d) for d in devices_from_db]
    )

    logger.debug(f"Returning {len(devices_to_return)} devices")

    return devices_to_return


def get_device_by_id(
    *, device_id: str, session: Session, device_manager: IDeviceManager
) -> Optional[DeviceWithStatus]:
    device = device_manager.get_device(device_id)
    device_from_db = session.get(Device, device_id)

    device_with_status: Optional[DeviceWithStatus] = None

    if device:
        logger.debug(f"Found connected device with id {device_id}")
        device_with_status = DeviceWithStatus(
            id=device.udid,
            udid=device.udid,
            **device.info.model_dump(),
            connected=True,
            status=device.status,
        )
        logger.debug(f"Adding or updating device in DB")
        session.add(_update_or_add(device_with_status, device_from_db))
        session.commit()
    elif device_from_db:
        logger.debug(f"Found device with id {device_id} in DB")
        device_with_status = DeviceWithStatus.model_validate(device_from_db)

    return device_with_status


def pair_device(*, device_id: str, device_manager: IDeviceManager):
    device = _get_connected_device_or_raise(device_id, device_manager)
    try:
        device.pair()
    except (
        core_device_exceptions.UserDeniedPairing,
        core_device_exceptions.PasswordRequired,
    ) as e:
        logger.error(f"Failed to pair device {device_id}", exc_info=e)

        raise HTTPException(
            status_code=400, detail="Pairing failed, user denied or password required"
        )


def unpair_device(*, device_id: str, device_manager: IDeviceManager):
    device = _get_connected_device_or_raise(device_id, device_manager)
    try:
        device.unpair()
    except (
        core_device_exceptions.DeviceNotPaired,
        core_device_exceptions.PairingError,
    ):
        logger.error(f"Unpairing failed for device {device_id}")

        raise HTTPException(
            status_code=400, detail="Device state does not allow unpairing"
        )


def enable_developer_mode(*, device_id: str, device_manager: IDeviceManager):
    device = _get_connected_device_or_raise(device_id, device_manager)

    try:
        device.enable_developer_mode()
    except (
        core_device_exceptions.DeveloperModeNotSupported,
        core_device_exceptions.DeveloperModeAlreadyEnabled,
        core_device_exceptions.DeviceHasPasscodeSet,
        core_device_exceptions.DeviceNotPaired,
    ) as e:
        logger.error(
            f"Failed to enable developer mode on device {device_id}", exc_info=e
        )

        raise HTTPException(status_code=400, detail="Failed to enable developer mode")


async def mount_ddi(*, device_id: str, device_manager: IDeviceManager):
    device = _get_connected_device_or_raise(device_id, device_manager)

    try:
        await device.mount_ddi()
    except (
        core_device_exceptions.DdiAlreadyMounted,
        core_device_exceptions.DeveloperModeNotEnabled,
        core_device_exceptions.DeveloperModeError,
        core_device_exceptions.DeviceNotPaired,
    ) as e:
        logger.error(f"Failed to mount DDI on device {device_id}", exc_info=e)

        raise HTTPException(
            status_code=400, detail="Device state does not allow mounting DDI"
        )


def unmount_ddi(*, device_id: str, device_manager: IDeviceManager):
    device = _get_connected_device_or_raise(device_id, device_manager)

    try:
        device.unmount_ddi()
    except (
        core_device_exceptions.DdiNotMounted,
        core_device_exceptions.DeveloperModeNotEnabled,
        core_device_exceptions.DeveloperModeError,
        core_device_exceptions.DeviceNotPaired,
    ) as e:
        logger.error(f"Failed to unmount DDI on device {device_id}", exc_info=e)

        raise HTTPException(
            status_code=400, detail="Device state does not allow unmounting DDI"
        )


async def connect_tunnel(*, device_id: str, device_manager: IDeviceManager):
    device = _get_connected_device_or_raise(device_id, device_manager)

    try:
        await device.establish_trusted_channel()
    except (
        core_device_exceptions.DeviceNotPaired,
        core_device_exceptions.DeveloperModeNotEnabled,
        core_device_exceptions.DdiNotMounted,
        core_device_exceptions.RsdNotSupported,
    ) as e:
        logger.error(f"Failed to connect tunnel on device {device_id}", exc_info=e)

        raise HTTPException(
            status_code=400, detail="Device state does not allow connecting tunnel"
        )


def _get_connected_device_or_raise(device_id: str, device_manager: IDeviceManager):
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


def _update_device_fields(device: Device, new_device: DeviceBase) -> Device:
    """
    Update the fields of a device with the fields of a new device without creating a new object.
    """
    return update_db_model(db_model=device, new_data_model=new_device)


def _update_or_add(
    device_with_status: DeviceWithStatus, device_from_db: Optional[Device] = None
) -> Device:
    if device_from_db:
        return _update_device_fields(device_from_db, device_with_status)
    return Device.model_validate(device_with_status)

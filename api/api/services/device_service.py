import logging
from typing import Optional

from core.device.i_device_manager import IDeviceManager
from sqlmodel import Session, select, col

from api.api_models import DeviceWithStatus
from api.db_models import Device, DeviceBase

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
    raise NotImplementedError


def unpair_device(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def enable_developer_mode(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def mount_ddi(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def unmount_ddi(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


async def connect_tunnel(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def _update_device_fields(device: Device, new_device: DeviceBase) -> Device:
    """
    Update the fields of a device with the fields of a new device without creating a new object.
    """
    validated_new_device = DeviceBase.model_validate(new_device)

    device.device_name = validated_new_device.device_name
    device.device_class = validated_new_device.device_class
    device.build_version = validated_new_device.build_version
    device.product_version = validated_new_device.product_version
    device.product_type = validated_new_device.product_type

    return device


def _update_or_add(
    device_with_status: DeviceWithStatus, device_from_db: Optional[Device] = None
) -> Device:
    if device_from_db:
        return _update_device_fields(device_from_db, device_with_status)
    return Device.model_validate(device_with_status)

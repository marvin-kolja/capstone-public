from fastapi import APIRouter, HTTPException

from api.api_models import DeviceWithStatus
from api.depends import SessionDep, DeviceManagerDep
from api.services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
async def list_devices(
    *, db_session: SessionDep, device_manager: DeviceManagerDep
) -> list[DeviceWithStatus]:
    """
    List all devices.
    """
    return device_service.list_devices(
        session=db_session, device_manager=device_manager
    )


@router.get("/{device_id}")
async def read_device(
    *, device_id: str, db_session: SessionDep, device_manager: DeviceManagerDep
) -> DeviceWithStatus:
    """
    Get the details of a device.
    """
    device = device_service.get_device_by_id(
        device_id=device_id, session=db_session, device_manager=device_manager
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/{device_id}/pair")
async def pair_device(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Start pairing process for a device.
    """
    return device_service.pair_device(
        device_id=device_id, device_manager=device_manager
    )


@router.post("/{device_id}/unpair")
async def unpair_device(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Unpair a device.
    """
    return device_service.unpair_device(
        device_id=device_id, device_manager=device_manager
    )


@router.post("/{device_id}/ddi/mount")
async def mount_ddi(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Mount a device DDI (Developer Disk Image).
    """
    return device_service.mount_ddi(device_id=device_id, device_manager=device_manager)


@router.post("/{device_id}/ddi/unmount")
async def unmount_ddi(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Unmount a device DDI (Developer Disk Image).
    """
    return device_service.unmount_ddi(
        device_id=device_id, device_manager=device_manager
    )


@router.post("/{device_id}/developer-mode/enable")
async def enable_developer_mode(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Enable developer mode on a device.
    """
    return device_service.enable_developer_mode(
        device_id=device_id, device_manager=device_manager
    )


@router.post("/{device_id}/tunnel/connect")
async def connect_tunnel(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Establish a tunnel connection to a device.
    """
    return device_service.connect_tunnel(
        device_id=device_id, device_manager=device_manager
    )

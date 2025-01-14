from fastapi import APIRouter

from api.api_models import DeviceWithStatus
from api.depends import SessionDep

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
async def list_devices(*, db_session: SessionDep) -> list[DeviceWithStatus]:
    """
    List all devices.
    """
    pass


@router.get("/{device_id}")
async def read_device(*, db_session: SessionDep, device_id: str) -> DeviceWithStatus:
    """
    Get the details of a device.
    """
    pass


@router.post("/{device_id}/pair")
async def pair_device(device_id: str):
    """
    Start pairing process for a device.
    """
    pass


@router.post("/{device_id}/unpair")
async def unpair_device(device_id: str):
    """
    Unpair a device.
    """
    pass


@router.post("/{device_id}/ddi/mount")
async def mount_ddi(device_id: str):
    """
    Mount a device DDI (Developer Disk Image).
    """
    pass


@router.post("/{device_id}/ddi/unmount")
async def unmount_ddi(device_id: str):
    """
    Unmount a device DDI (Developer Disk Image).
    """
    pass


@router.post("/{device_id}/developer-mode/enable")
async def enable_developer_mode(device_id: str):
    """
    Enable developer mode on a device.
    """
    pass


@router.post("/{device_id}/developer-mode/disable")
async def disable_developer_mode(device_id: str):
    """
    Disable developer mode on a device.
    """
    pass


@router.post("/{device_id}/tunnel/connect")
async def connect_tunnel(device_id: str):
    """
    Establish a tunnel connection to a device.
    """
    pass


@router.post("/{device_id}/tunnel/close")
async def close_tunnel(device_id: str):
    """
    Close a tunnel connection to a device.
    """
    pass

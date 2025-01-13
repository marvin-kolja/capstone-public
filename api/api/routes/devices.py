from fastapi import APIRouter

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
async def list_devices():
    """
    List all devices.
    """
    pass


@router.get("/{device_id}")
async def read_device(device_id: int):
    """
    Get the details of a device.
    """
    pass


@router.post("/{device_id}/pair")
async def pair_device(device_id: int):
    """
    Start pairing process for a device.
    """
    pass


@router.post("/{device_id}/unpair")
async def unpair_device(device_id: int):
    """
    Unpair a device.
    """
    pass


@router.post("/{device_id}/ddi/mount")
async def mount_ddi(device_id: int):
    """
    Mount a device DDI (Developer Disk Image).
    """
    pass


@router.post("/{device_id}/ddi/unmount")
async def unmount_ddi(device_id: int):
    """
    Unmount a device DDI (Developer Disk Image).
    """
    pass


@router.post("/{device_id}/developer-mode/enable")
async def enable_developer_mode(device_id: int):
    """
    Enable developer mode on a device.
    """
    pass


@router.post("/{device_id}/developer-mode/disable")
async def disable_developer_mode(device_id: int):
    """
    Disable developer mode on a device.
    """
    pass


@router.post("/{device_id}/tunnel/connect")
async def connect_tunnel(device_id: int):
    """
    Establish a tunnel connection to a device.
    """
    pass


@router.post("/{device_id}/tunnel/close")
async def close_tunnel(device_id: int):
    """
    Close a tunnel connection to a device.
    """
    pass

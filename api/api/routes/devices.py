from core.device.i_device_manager import IDeviceManager
from fastapi import APIRouter, HTTPException

from api.custom_responses import build_common_http_exception_responses
from api.models import DeviceWithStatus
from api.depends import AsyncSessionDep, DeviceManagerDep
from api.services import device_service
from core.exceptions import i_device as core_device_exceptions

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get(
    "/",
    responses=build_common_http_exception_responses([500]),
)
async def list_devices(
    *,
    db_session: AsyncSessionDep,
    device_manager: DeviceManagerDep,
) -> list[DeviceWithStatus]:
    """
    List all devices.
    """
    return await device_service.list_devices(
        session=db_session, device_manager=device_manager
    )


@router.get(
    "/{device_id}",
    responses=build_common_http_exception_responses([404, 422, 500]),
)
async def read_device(
    *, device_id: str, db_session: AsyncSessionDep, device_manager: DeviceManagerDep
) -> DeviceWithStatus:
    """
    Get the details of a device.
    """
    device = await device_service.get_device_by_id(
        device_id=device_id, session=db_session, device_manager=device_manager
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post(
    "/{device_id}/pair",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def pair_device(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Start pairing process for a device.
    """
    try:
        device_service.pair_device(
            device=_get_i_device_or_raise(device_id, device_manager)
        )
    except Exception as e:
        _handle_core_device_exceptions(e)


@router.post(
    "/{device_id}/unpair",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def unpair_device(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Unpair a device.
    """
    try:
        device_service.unpair_device(
            device=_get_i_device_or_raise(device_id, device_manager)
        )
    except Exception as e:
        _handle_core_device_exceptions(e)


@router.post(
    "/{device_id}/ddi/mount",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def mount_ddi(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Mount a device DDI (Developer Disk Image).
    """
    try:

        await device_service.mount_ddi(
            device=_get_i_device_or_raise(device_id, device_manager)
        )
    except Exception as e:
        _handle_core_device_exceptions(e)


@router.post(
    "/{device_id}/ddi/unmount",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def unmount_ddi(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Unmount a device DDI (Developer Disk Image).
    """
    try:
        device_service.unmount_ddi(
            device=_get_i_device_or_raise(device_id, device_manager)
        )
    except Exception as e:
        _handle_core_device_exceptions(e)


@router.post(
    "/{device_id}/developer-mode/enable",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def enable_developer_mode(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Enable developer mode on a device.
    """
    try:
        device_service.enable_developer_mode(
            device=_get_i_device_or_raise(device_id, device_manager)
        )
    except Exception as e:
        _handle_core_device_exceptions(e)


@router.post(
    "/{device_id}/tunnel/connect",
    responses=build_common_http_exception_responses([400, 404, 422, 500]),
)
async def connect_tunnel(*, device_id: str, device_manager: DeviceManagerDep):
    """
    Establish a tunnel connection to a device.
    """
    try:
        await device_service.connect_tunnel(
            device=_get_i_device_or_raise(device_id, device_manager)
        )
    except Exception as e:
        _handle_core_device_exceptions(e)


def _handle_core_device_exceptions(e: Exception):
    """
    Transforms some core device exceptions into HTTPExceptions.

    :raises HTTPException: If the exception is one of the handled exceptions
    :raises Exception: Re-raises the exception if it's not one of the handled exceptions
    """

    if isinstance(e, core_device_exceptions.DeviceNotPaired):
        raise HTTPException(
            status_code=400,
            detail="Device is not paired",
        ) from e
    if isinstance(e, core_device_exceptions.UserDeniedPairing):
        raise HTTPException(
            status_code=400,
            detail="User denied pairing",
        ) from e
    if isinstance(e, core_device_exceptions.PasswordRequired):
        raise HTTPException(
            status_code=400,
            detail="Device requires password for pairing",
        ) from e
    if isinstance(e, core_device_exceptions.DdiNotMounted):
        raise HTTPException(
            status_code=400,
            detail="DDI is not mounted",
        ) from e
    if isinstance(e, core_device_exceptions.DdiAlreadyMounted):
        raise HTTPException(
            status_code=400,
            detail="DDI is already mounted",
        ) from e
    if isinstance(e, core_device_exceptions.DeveloperModeNotEnabled):
        raise HTTPException(
            status_code=400,
            detail="Developer mode is not enabled",
        ) from e
    if isinstance(e, core_device_exceptions.DeveloperModeNotSupported):
        raise HTTPException(
            status_code=400,
            detail="Developer mode is not supported on this device",
        ) from e
    if isinstance(e, core_device_exceptions.DeveloperModeAlreadyEnabled):
        raise HTTPException(
            status_code=400,
            detail="Developer mode is already enabled",
        ) from e
    if isinstance(e, core_device_exceptions.DeviceHasPasscodeSet):
        raise HTTPException(
            status_code=400,
            detail="Device has a passcode set",
        ) from e
    if isinstance(e, core_device_exceptions.RsdNotSupported):
        raise HTTPException(
            status_code=400,
            detail="Device does not support RSD",
        ) from e

    raise e  # Re-raise the exception if it's not one of the above


def _get_i_device_or_raise(device_id: str, device_manager: IDeviceManager):
    """
    Get a connected device by id or raise an HTTPException if the device is not found.

    :raises HTTPException: If the device is not found
    """
    device = device_manager.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device is not connected")
    return device

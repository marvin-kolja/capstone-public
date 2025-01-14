from core.device.i_device_manager import IDeviceManager
from sqlmodel import Session

from api.api_models import DeviceWithStatus


def list_devices(
    *, db_session: Session, device_manager: IDeviceManager
) -> list[DeviceWithStatus]:
    raise NotImplementedError


def get_device_by_id(
    *, device_id: str, db_session: Session, device_manager: IDeviceManager
) -> DeviceWithStatus:
    raise NotImplementedError


def pair_device(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def unpair_device(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def enable_developer_mode(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def disable_developer_mode(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def mount_ddi(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def unmount_ddi(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def connect_tunnel(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError


def disconnect_tunnel(*, device_id: str, device_manager: IDeviceManager):
    raise NotImplementedError

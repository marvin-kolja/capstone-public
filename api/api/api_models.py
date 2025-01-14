from typing import Optional

from core.device.i_device import IDeviceStatus

from api.db_models import DeviceBase


class DeviceWithStatus(DeviceBase):
    id: str
    udid: str

    connected: bool = False
    status: Optional[IDeviceStatus] = None

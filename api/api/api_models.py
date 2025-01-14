from typing import Optional

from core.device.i_device import IDeviceStatus

from api.db_models import Device


class DeviceResponse(Device):
    connected: bool = False
    status: Optional[IDeviceStatus] = None

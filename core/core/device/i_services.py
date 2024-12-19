from core.device.i_device import IDevice
from core.device.services_protocol import ServicesProtocol


class IServices(ServicesProtocol):
    def __init__(self, device: IDevice):
        self.__device = device

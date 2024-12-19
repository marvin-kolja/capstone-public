import logging
from typing import Callable

from pymobiledevice3.services.installation_proxy import InstallationProxyService

from core.device.i_device import IDevice
from core.device.services_protocol import ServicesProtocol

logger = logging.getLogger(__name__)


class IServices(ServicesProtocol):
    def __init__(self, device: IDevice):
        self.__device = device

    @property
    def _installer(self) -> InstallationProxyService:
        return InstallationProxyService(lockdown=self.__device.lockdown_service)

    def install_app(self, app_path: str, progress_callback: Callable[[str], None] = None):
        raise NotImplementedError

    def uninstall_app(self, bundle_id: str, progress_callback: Callable[[str], None] = None):
        raise NotImplementedError

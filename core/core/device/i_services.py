import logging
from typing import Callable

from pymobiledevice3.services.installation_proxy import InstallationProxyService

from core.device.i_device import IDevice
from core.device.services_protocol import ServicesProtocol
from core.exceptions.i_device import AppInstallError, AppUninstallError

logger = logging.getLogger(__name__)


class IServices(ServicesProtocol):
    def __init__(self, device: IDevice):
        self.__device = device

    @property
    def _installer(self) -> InstallationProxyService:
        return InstallationProxyService(lockdown=self.__device.lockdown_service)

    def install_app(self, app_path: str, progress_callback: Callable[[str], None] = None):
        """
        Install app onto device.

        :param app_path: Path to ipa.
        :param progress_callback: Function to call with install progress.

        :raises AppInstallError: If app installation fails.
        """
        try:
            logger.debug(f"Installing app onto device using path: {app_path}")
            self._installer.install(app_path, handler=progress_callback)
        except Exception as e:
            logger.error(f"Failed to install app onto device using path: {app_path}, error: {e}")
            raise AppInstallError from e

    def uninstall_app(self, bundle_id: str, progress_callback: Callable[[str], None] = None):
        """
        Uninstall app from device.

        :param bundle_id: Bundle ID to uninstall.
        :param progress_callback: Function to call with uninstall progress.

        :raises AppUninstallError: If app uninstallation fails.
        """
        try:
            logger.debug(f"Uninstalling app from device using bundle_id: {bundle_id}")
            self._installer.uninstall(bundle_id, handler=progress_callback)
        except Exception as e:
            logger.error(f"Failed to uninstall app from device using bundle_id: {bundle_id}, error: {e}")
            raise AppUninstallError from e

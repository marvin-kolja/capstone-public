import asyncio
import contextlib
import logging
from typing import Callable, Optional

from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import (
    DvtSecureSocketProxyService,
)
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from core.device.i_device import IDevice
from core.device.services_protocol import ServicesProtocol
from core.exceptions.i_device import AppInstallError, AppUninstallError, AppListError

logger = logging.getLogger(__name__)


class IServices(ServicesProtocol):
    def __init__(self, device: IDevice):
        self.__device = device

    @property
    def _installer(self) -> InstallationProxyService:
        return InstallationProxyService(lockdown=self.__device.lockdown_service)

    @property
    @contextlib.contextmanager
    def _dvt(self) -> DvtSecureSocketProxyService:
        with DvtSecureSocketProxyService(
            lockdown=self.__device.lockdown_service
        ) as dvt:
            yield dvt

    def install_app(
        self, app_path: str, progress_callback: Callable[[str], None] = None
    ):
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
            logger.error(
                f"Failed to install app onto device using path: {app_path}, error: {e}"
            )
            raise AppInstallError from e

    def uninstall_app(
        self, bundle_id: str, progress_callback: Callable[[str], None] = None
    ):
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
            logger.error(
                f"Failed to uninstall app from device using bundle_id: {bundle_id}, error: {e}"
            )
            raise AppUninstallError from e

    def list_installed_apps(self) -> list[str]:
        """
        List all installed apps on the device by returning their bundle IDs.

        :return: A list of bundle IDs for all installed apps.
        """
        try:
            logger.debug(
                f"Listing installed applications on device {self.__device.lockdown_service.udid}"
            )
            apps = self._installer.get_apps()
            bundle_ids = apps.keys()
            return list(bundle_ids)
        except Exception as e:
            logger.error(
                f"Failed to list apps on device {self.__device.lockdown_service.udid}, error: {e}"
            )
            raise AppListError from e

    def launch_app(self, bundle_id: str) -> int:
        """
        Launches an app using the bundle ID.

        :param bundle_id: The bundle id of the app to launch
        """
        with self._dvt as dvt:
            return ProcessControl(dvt).launch(bundle_id)

    def terminate_app(self, bundle_id: str):
        """
        Terminates an app using the bundle ID.

        Termination is done by sending a SIGKILL signal to the app's process.

        NOTE: While SIGTERM would signal the app to gracefully terminate, it was observed that the app would not
        terminate in some cases. Hence, SIGKILL is used to ensure the app is terminated.

        :param bundle_id: The bundle id of the app to terminate
        """
        with self._dvt as dvt:
            if pid := self.pid_for_app(bundle_id):
                ProcessControl(dvt).signal(pid=pid, sig=9)

    def pid_for_app(self, bundle_id: str) -> Optional[int]:
        """
        Tries to get the PID for an app using the bundle ID.

        :param bundle_id: The bundle id of the app to get the PID for

        :return: The PID of the app or None if the PID could not be retrieved
        """
        with self._dvt as dvt:
            pid = ProcessControl(dvt).process_identifier_for_bundle_identifier(
                bundle_id
            )
            if pid == 0:
                return None
            return pid

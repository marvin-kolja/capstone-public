from unittest.mock import patch, MagicMock

import pytest
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from core.device.i_services import IServices
from core.exceptions.i_device import AppInstallError, AppUninstallError, AppListError


@pytest.fixture
def services(i_device):
    return IServices(i_device)


@pytest.fixture
def mock_installer(services):
    with patch.object(
        type(services), "_installer", MagicMock(spec=InstallationProxyService)
    ) as mock:
        yield mock


@pytest.fixture
def mock_dvt():
    with patch("core.device.i_services.DvtSecureSocketProxyService") as mock:
        yield mock


@pytest.fixture
def mock_process_control():
    with patch("core.device.i_services.ProcessControl") as mock:
        yield mock


@pytest.mark.parametrize(
    "paired,developer_mode_enabled,product_version", [(True, True, "18.0")]
)
class TestIServices:
    def test_install_exception(self, services, mock_installer):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `install_app` method of an `IServices` instance
        AND: The `InstallationProxyService.install` method raised an exception

        THEN: The `AppInstallError` exception is raised
        """
        app_path = "/tmp/some_app"

        mock_installer.install.side_effect = Exception

        with pytest.raises(AppInstallError):
            services.install_app(app_path)

    def test_uninstall_exception(self, services, mock_installer):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `uninstall_app` method of an `IServices` instance
        AND: The `InstallationProxyService.uninstall` method raised an exception

        THEN: The `AppUninstallError` exception is raised
        """
        bundle_id = "some_bundle_id"
        mock_installer.uninstall.side_effect = Exception

        with pytest.raises(AppUninstallError):
            services.uninstall_app(bundle_id)

    def test_list_installed_apps(self, services, mock_installer):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `list_installed_apps` method of an `IServices` instance

        THEN: The `InstallationProxyService.get_apps` method is called
        """
        services.list_installed_apps()

        mock_installer.get_apps.assert_called_once()

    def test_list_installed_apps_exception(self, services, mock_installer):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `list_installed_apps` method of an `IServices` instance
        AND: The `InstallationProxyService.get_apps` method raised an exception

        THEN: The `AppListError` exception is raised
        """
        mock_installer.get_apps.side_effect = Exception

        with pytest.raises(AppListError):
            services.list_installed_apps()

    def test_launch_app(self, services, i_device, mock_dvt, mock_process_control):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `launch_app` method of an `IServices` instance

        THEN: The `ProcessControl.launch` method is called
        AND: The `DvtSecureSocketProxyService` is created and used as a context manager
        """
        bundle_id = "some_bundle_id"
        services.launch_app(bundle_id)

        mock_dvt.assert_called_once_with(lockdown=i_device.lockdown_service)
        mock_dvt.return_value.__enter__.assert_called_once()
        mock_dvt.return_value.__exit__.assert_called_once()
        mock_process_control.return_value.launch.assert_called_once_with(bundle_id)

    def test_terminate_app(self, services, i_device, mock_dvt, mock_process_control):
        """
        GIVEN: An `IServices` instance
        AND: A mocked `IServices.pid_for_app` method that returns a PID

        WHEN: Calling the `terminate_app` method of an `IServices` instance

        THEN: The `ProcessControl.signal` method is called with signal 9 (SIGKILL)
        AND: The `DvtSecureSocketProxyService` is created and used as a context manager
        """
        bundle_id = "some_bundle_id"

        with patch.object(services, "pid_for_app", return_value=123):
            services.terminate_app(bundle_id)

            mock_dvt.assert_called_once_with(lockdown=i_device.lockdown_service)
            mock_dvt.return_value.__enter__.assert_called_once()
            mock_dvt.return_value.__exit__.assert_called_once()
            mock_process_control.return_value.signal.assert_called_once_with(
                pid=123, sig=9
            )

    def test_pid_for_app(self, services, i_device, mock_dvt, mock_process_control):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `pid_for_app` method of an `IServices` instance

        THEN: The `ProcessControl.process_identifier_for_bundle_identifier` method is called
        AND: The `DvtSecureSocketProxyService` is created and used as a context manager
        """
        bundle_id = "some_bundle_id"
        services.pid_for_app(bundle_id)

        mock_dvt.assert_called_once_with(lockdown=i_device.lockdown_service)
        mock_dvt.return_value.__enter__.assert_called_once()
        mock_dvt.return_value.__exit__.assert_called_once()
        mock_process_control.return_value.process_identifier_for_bundle_identifier.assert_called_once_with(
            bundle_id
        )

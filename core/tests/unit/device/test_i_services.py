from unittest.mock import patch, MagicMock, PropertyMock

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

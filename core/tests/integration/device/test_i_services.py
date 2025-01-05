import pytest

from core.device.i_device_manager import IDeviceManager
from core.device.i_services import IServices


class TestIServices:

    @pytest.mark.real_device
    def test_list_installed_apps_contains_ios_phone_app(self, device_udid):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `list_installed_apps` method of an `IServices` instance

        THEN: The list of installed apps contains the iOS Phone app
        """
        device = IDeviceManager().get_device(udid=device_udid)
        services = IServices(device=device)

        bundle_ids = services.list_installed_apps()

        assert "com.apple.mobilephone" in bundle_ids

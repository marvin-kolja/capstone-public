from datetime import timedelta

import pytest

from core.device.i_device_manager import IDeviceManager
from core.device.i_services import IServices


class TestIServices:
    @pytest.mark.real_device
    def test_uninstall_app_non_existing(self, device_udid):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `uninstall_app` method with a non-existing bundle ID

        THEN: No exception is raised
        """
        device = IDeviceManager().get_device(udid=device_udid)
        services = IServices(device=device)

        services.uninstall_app(bundle_id="non.existing.bundle.id")

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

    @pytest.mark.real_device
    @pytest.mark.requires_sudo
    @pytest.mark.asyncio
    async def test_launching_and_terminating_ios_phone_app(
        self, tunnel_server_subprocess, device_udid
    ):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `launch_app` method of an `IServices` instance
        AND: Calling the `terminate_app` method of an `IServices` instance

        THEN: The iOS Phone app is launched and terminated successfully in between the calls
        """
        phone_bundle_id = "com.apple.mobilephone"

        # Prepare the device for use with dvt
        device = IDeviceManager().get_device(udid=device_udid)
        if device.requires_tunnel_for_developer_tools:
            await device.establish_trusted_channel()

        services = IServices(device=device)

        services.launch_app(bundle_id=phone_bundle_id)
        assert services.pid_for_app(bundle_id=phone_bundle_id) is not None
        services.terminate_app(bundle_id=phone_bundle_id)
        assert services.pid_for_app(bundle_id=phone_bundle_id) is None

    @pytest.mark.real_device
    @pytest.mark.requires_sudo
    @pytest.mark.asyncio
    async def test_wait_for_app_pid(self, tunnel_server_subprocess, device_udid):
        """
        GIVEN: An `IServices` instance

        WHEN: Calling the `wait_for_app_pid` method of an `IServices` instance

        THEN: The iOS Phone app is launched and terminated successfully in between the calls
        """
        phone_bundle_id = "invalid.bundle.id"

        # Prepare the device for use with dvt
        device = IDeviceManager().get_device(udid=device_udid)
        if device.requires_tunnel_for_developer_tools:
            await device.establish_trusted_channel()

        services = IServices(device=device)

        with pytest.raises(TimeoutError):
            await services.wait_for_app_pid(
                bundle_id=phone_bundle_id,
                timeout=timedelta(milliseconds=100),
                frequency=timedelta(milliseconds=100),
            )

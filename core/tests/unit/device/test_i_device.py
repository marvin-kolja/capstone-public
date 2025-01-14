from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from packaging.version import Version
from pymobiledevice3 import exceptions as pmd3_exceptions
from pymobiledevice3.exceptions import DeviceHasPasscodeSetError
from pymobiledevice3.lockdown import UsbmuxLockdownClient
from pymobiledevice3.remote.remote_service_discovery import (
    RemoteServiceDiscoveryService,
)
from pymobiledevice3.services.mobile_image_mounter import MobileImageMounterService

from core.codec.socket_json_codec import SuccessResponse
from core.device.i_device import IDevice, IDeviceStatus
from core.exceptions.i_device import (
    PairingError,
    DeveloperModeNotEnabled,
    DeveloperModeNotSupported,
    DeveloperModeAlreadyEnabled,
    DeviceNotPaired,
    UserDeniedPairing,
    PasswordRequired,
    DeveloperModeError,
    DdiNotMounted,
    DdiAlreadyMounted,
    DdiMountingError,
    DeviceHasPasscodeSet,
    RsdNotSupported,
    DeviceNotReadyForDvt,
    RsdNotConnected,
)


@pytest.fixture()
def patched_i_device_mounter(i_device_mocked_lockdown):
    with patch.object(
        IDevice, "_mounter", MagicMock(spec=MobileImageMounterService)
    ) as mock_mounter:
        yield mock_mounter


@pytest.mark.parametrize("developer_mode_enabled,product_version", [(False, "18.0")])
class TestIDevicePairing:
    @pytest.mark.parametrize("paired", [True, False])
    class TestParametrized:
        """
        GIVEN: Various conditions for pairing and other states.
        """

        def test_check_paired(self, i_device_mocked_lockdown, paired):
            """
            WHEN: check_paired is called.

            THEN:
                - If device is not paired (paired=False), a PairingError should be raised.
                - If device is paired (paired=True), no error should be raised.
            """
            if not paired:
                with pytest.raises(PairingError):
                    i_device_mocked_lockdown.check_paired()
            else:
                i_device_mocked_lockdown.check_paired()

        def test_pair_behavior(
            self, i_device_mocked_lockdown, mock_usbmux_lockdown_client
        ):
            """
            WHEN: pair is called

            THEN: The `LockdownClient.pair` method should be called regardless of the current state.
            """
            i_device_mocked_lockdown.pair()

            mock_usbmux_lockdown_client.pair.assert_called_once()

        def test_unpair_behavior(
            self, i_device_mocked_lockdown, paired, mock_usbmux_lockdown_client
        ):
            """
            WHEN: unpair is called

            THEN:
                - If already unpaired, `LockdownClient.unpair` method should not be called again.
                    - And a `DeviceNotPaired` exception should be raised.
                - If paired, `LockdownClient.unpair` method should be called once.
            """
            if paired:
                i_device_mocked_lockdown.unpair()
                mock_usbmux_lockdown_client.unpair.assert_called_once()
            else:
                with pytest.raises(DeviceNotPaired):
                    i_device_mocked_lockdown.unpair()
                mock_usbmux_lockdown_client.unpair.assert_not_called()

    @pytest.mark.parametrize("paired", [False])
    def test_pair_user_denied(
        self, i_device_mocked_lockdown, mock_usbmux_lockdown_client, paired
    ):
        """
        GIVEN: A device that is not paired.

        WHEN: pair is called.
        AND: The user denies the pairing request.

        THEN: A `UserDeniedPairing` exception should be raised.
        """
        mock_usbmux_lockdown_client.pair.side_effect = (
            pmd3_exceptions.UserDeniedPairingError
        )
        with pytest.raises(UserDeniedPairing):
            i_device_mocked_lockdown.pair()

    @pytest.mark.parametrize("paired", [False])
    def test_pair_password_required(
        self, i_device_mocked_lockdown, mock_usbmux_lockdown_client, paired
    ):
        """
        GIVEN: A device that is not paired.

        WHEN: pair is called.
        AND: A password is required to pair with the device.

        THEN: A `PasswordRequired` exception should be raised.
        """
        mock_usbmux_lockdown_client.pair.side_effect = (
            pmd3_exceptions.PasswordRequiredError
        )
        with pytest.raises(PasswordRequired):
            i_device_mocked_lockdown.pair()

    @pytest.mark.parametrize("paired", [False])
    def test_pair_other_error(
        self, i_device_mocked_lockdown, mock_usbmux_lockdown_client, paired
    ):
        """
        GIVEN: A device that is not paired.

        WHEN: pair is called.
        AND: An unexpected error occurs.

        THEN: A `PairingError` exception should be raised.
        """
        mock_usbmux_lockdown_client.pair.side_effect = Exception
        with pytest.raises(PairingError):
            i_device_mocked_lockdown.pair()

    @pytest.mark.parametrize("paired", [True])
    def test_unpair_other_error(
        self, i_device_mocked_lockdown, mock_usbmux_lockdown_client, paired
    ):
        """
        GIVEN: A device that is paired.

        WHEN: unpair is called.
        AND: An unexpected error occurs.

        THEN: A `PairingError` exception should be raised.
        """
        mock_usbmux_lockdown_client.unpair.side_effect = Exception
        with pytest.raises(PairingError):
            i_device_mocked_lockdown.unpair()


class TestIDeviceDeveloperMode:
    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled",
        [
            (False, "15.0", None),
            (True, "15.0", None),
            (False, "16.0", None),
            (True, "16.0", False),
            (True, "16.0", True),
        ],
    )
    class TestParametrized:
        """
        GIVEN: Various conditions for developer mode and other states
        """

        def test_check_developer_mode(
            self,
            i_device_mocked_lockdown,
            mock_usbmux_lockdown_client,
            paired,
            developer_mode_enabled,
        ):
            """
            WHEN: check_developer_mode_enabled is called

            THEN:
                - If product_version < 16.0, DeveloperModeNotSupported is raised.
                - Else if not paired, NotPairedError is raised.
                - Else if developer_mode_enabled=False, DeveloperModeNotEnabled is raised.
                - Else, no exception is raised.
            """
            if Version(mock_usbmux_lockdown_client.product_version) < Version("16.0"):
                with pytest.raises(DeveloperModeNotSupported):
                    i_device_mocked_lockdown.check_developer_mode_enabled()
            elif not paired:
                with pytest.raises(DeviceNotPaired):
                    i_device_mocked_lockdown.check_developer_mode_enabled()
            elif not developer_mode_enabled:
                with pytest.raises(DeveloperModeNotEnabled):
                    i_device_mocked_lockdown.check_developer_mode_enabled()
            else:
                i_device_mocked_lockdown.check_developer_mode_enabled()

        def test_enable_developer_mode(
            self,
            i_device_mocked_lockdown,
            mock_usbmux_lockdown_client,
            paired,
            developer_mode_enabled,
        ):
            """
            WHEN: enable_developer_mode is called

            THEN:
                - If product_version < 16.0, DeveloperModeNotSupported is raised.
                - Else if not paired, NotPairedError is raised.
                - Else if developer_mode_enabled=True, DeveloperModeAlreadyEnabled is raised.
                - Else, no exception is raised
                    - And `AmfiService.enable_developer_mode` should be called.
            """
            with patch(
                "core.device.i_device.AmfiService.enable_developer_mode",
                return_value=None,
            ) as mock_enable_developer_mode:
                if Version(mock_usbmux_lockdown_client.product_version) < Version(
                    "16.0"
                ):
                    with pytest.raises(DeveloperModeNotSupported):
                        i_device_mocked_lockdown.enable_developer_mode()
                elif not paired:
                    with pytest.raises(DeviceNotPaired):
                        i_device_mocked_lockdown.enable_developer_mode()
                elif developer_mode_enabled:
                    with pytest.raises(DeveloperModeAlreadyEnabled):
                        i_device_mocked_lockdown.enable_developer_mode()
                else:
                    i_device_mocked_lockdown.enable_developer_mode()
                    mock_enable_developer_mode.assert_called_once()

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled", [(True, "16.0", False)]
    )
    def test_enable_developer_mode_unexpected_error(
        self,
        i_device_mocked_lockdown,
        mock_usbmux_lockdown_client,
        paired,
        developer_mode_enabled,
        product_version,
    ):
        """
        GIVEN: A device that is paired and has product version >= 16.0.

        WHEN: enable_developer_mode is called.
        AND: An unexpected error occurs.

        THEN: A `DeveloperModeError` exception should be raised.
        AND: `AmfiService.enable_developer_mode` should be called.
        """
        with patch(
            "core.device.i_device.AmfiService.enable_developer_mode",
            side_effect=Exception,
        ) as mock_enable_developer_mode:
            with pytest.raises(DeveloperModeError):
                i_device_mocked_lockdown.enable_developer_mode()
            mock_enable_developer_mode.assert_called_once()

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled", [(True, "16.0", False)]
    )
    def test_enable_developer_mode_passcode_set_error(
        self,
        i_device_mocked_lockdown,
        mock_usbmux_lockdown_client,
        paired,
        developer_mode_enabled,
        product_version,
    ):
        """
        GIVEN: A device that is paired and has product version >= 16.0.

        WHEN: enable_developer_mode is called.
        AND: An error occurs because the device has a passcode set.

        THEN: A `DeviceHasPasscodeSet` exception should be raised.
        """
        with patch(
            "core.device.i_device.AmfiService.enable_developer_mode",
            side_effect=DeviceHasPasscodeSetError,
        ) as mock_enable_developer_mode:
            with pytest.raises(DeviceHasPasscodeSet):
                i_device_mocked_lockdown.enable_developer_mode()
            mock_enable_developer_mode.assert_called_once()

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled", [(True, "16.0", False)]
    )
    def test_check_developer_mode_unexpected_error(
        self,
        i_device_mocked_lockdown,
        mock_usbmux_lockdown_client,
        paired,
        developer_mode_enabled,
        product_version,
    ):
        """
        GIVEN: A device that is paired and has product version >= 16.0.

        WHEN: check_developer_mode_enabled is called.
        AND: An unexpected error occurs.

        THEN: A `DeveloperModeError` exception should be raised.
        """
        type(mock_usbmux_lockdown_client).developer_mode_status = PropertyMock(
            side_effect=Exception
        )

        with pytest.raises(DeveloperModeError):
            i_device_mocked_lockdown.check_developer_mode_enabled()


class TestIDeviceDdiMounting:
    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,ddi_mounted",
        [
            (False, "15.0", None, None),
            (True, "15.0", None, None),
            (True, "15.0", None, True),
            (False, "16.0", None, None),
            (True, "16.0", False, None),
            (True, "16.0", True, False),
            (True, "16.0", True, True),
        ],
    )
    class TestParametrized:
        """
        GIVEN: Various conditions for developer mode and other states
        """

        def test_check_ddi_mounted(
            self,
            i_device_mocked_lockdown,
            paired,
            developer_mode_enabled,
            product_version,
            ddi_mounted,
            patched_i_device_mounter,
        ):
            """
            WHEN: check_ddi_mounted is called

            THEN:
                - If not paired, NotPairedError is raised.
                - If developer_mode_enabled=False and product_version >= 16.0, DeveloperModeNotEnabled is raised.
                - Else if ddi_mounted=False, DdiNotMounted is raised.
                - Else, no exception is raised.
            """
            patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted

            if not paired:
                with pytest.raises(DeviceNotPaired):
                    i_device_mocked_lockdown.check_ddi_mounted()
            elif not developer_mode_enabled and Version(product_version) >= Version(
                "16.0"
            ):
                with pytest.raises(DeveloperModeNotEnabled):
                    i_device_mocked_lockdown.check_ddi_mounted()
            elif not ddi_mounted:
                with pytest.raises(DdiNotMounted):
                    i_device_mocked_lockdown.check_ddi_mounted()
            else:
                i_device_mocked_lockdown.check_ddi_mounted()

        @pytest.mark.asyncio
        async def test_mount_ddi(
            self,
            i_device_mocked_lockdown,
            paired,
            developer_mode_enabled,
            product_version,
            ddi_mounted,
            patched_i_device_mounter,
        ):
            """
            WHEN: mount_ddi is called

            THEN:
                - If not paired, NotPairedError is raised.
                - If developer_mode_enabled=False and product_version >= 16.0, DeveloperModeNotEnabled is raised.
                - Else if ddi_mounted=True, DdiAlreadyMounted is raised.
                - Else, no exception is raised.
                    - And `MobileImageMounterService.mount_image` should be called.
            """
            with patch(
                "core.device.i_device.auto_mount", return_value=None
            ) as mock_auto_mount:
                patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted

                if not paired:
                    with pytest.raises(DeviceNotPaired):
                        await i_device_mocked_lockdown.mount_ddi()
                elif not developer_mode_enabled and Version(product_version) >= Version(
                    "16.0"
                ):
                    with pytest.raises(DeveloperModeNotEnabled):
                        await i_device_mocked_lockdown.mount_ddi()
                elif ddi_mounted:
                    with pytest.raises(DdiAlreadyMounted):
                        await i_device_mocked_lockdown.mount_ddi()
                else:
                    await i_device_mocked_lockdown.mount_ddi()
                    mock_auto_mount.assert_called_once()

        def test_unmount_ddi(
            self,
            i_device_mocked_lockdown,
            paired,
            developer_mode_enabled,
            product_version,
            ddi_mounted,
            patched_i_device_mounter,
        ):
            """
            WHEN: unmount_ddi is called

            THEN:
                - If not paired, NotPairedError is raised.
                - If developer_mode_enabled=False and product_version >= 16.0, DeveloperModeNotEnabled is raised.
                - Else if ddi_mounted=False, DdiNotMounted is raised.
                - Else, no exception is raised.
                    - And `MobileImageMounterService.unmount_image` should be called.
            """
            patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted
            if not paired:
                with pytest.raises(DeviceNotPaired):
                    i_device_mocked_lockdown.unmount_ddi()
            elif not developer_mode_enabled and Version(product_version) >= Version(
                "16.0"
            ):
                with pytest.raises(DeveloperModeNotEnabled):
                    i_device_mocked_lockdown.unmount_ddi()
            elif not ddi_mounted:
                with pytest.raises(DdiNotMounted):
                    i_device_mocked_lockdown.unmount_ddi()
            else:
                i_device_mocked_lockdown.unmount_ddi()
                patched_i_device_mounter.unmount_image.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,ddi_mounted",
        [(True, "16.0", True, False)],
    )
    async def test_mount_ddi_unexpected_error(
        self,
        i_device_mocked_lockdown,
        paired,
        developer_mode_enabled,
        product_version,
        ddi_mounted,
        patched_i_device_mounter,
    ):
        """
        GIVEN: A device that is paired
        AND: Has developer mode enabled
        AND: Its product version is >= 16.0.

        WHEN: mount_ddi is called.
        AND: An unexpected error occurs.

        THEN: A `DdiMountingError` exception should be raised.
        AND: `MobileImageMounterService.mount_image` should be called.
        """
        with patch(
            "core.device.i_device.auto_mount", side_effect=Exception
        ) as mock_auto_mount:
            patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted

            with pytest.raises(DdiMountingError):
                await i_device_mocked_lockdown.mount_ddi()
            mock_auto_mount.assert_called_once()

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,ddi_mounted",
        [(True, "16.0", True, True)],
    )
    def test_unmount_ddi_unexpected_error(
        self,
        i_device_mocked_lockdown,
        paired,
        developer_mode_enabled,
        product_version,
        ddi_mounted,
        patched_i_device_mounter,
    ):
        """
        GIVEN: A device that is paired
        AND: Has developer mode enabled
        AND: Its product version is >= 16.0
        AND: Developer Disk Image is mounted.

        WHEN: unmount_ddi is called.
        AND: An unexpected error occurs.

        THEN: A `DdiMountingError` exception should be raised.
        AND: `MobileImageMounterService.unmount_image` should be called.
        """
        patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted
        patched_i_device_mounter.unmount_image.side_effect = Exception

        with pytest.raises(DdiMountingError):
            i_device_mocked_lockdown.unmount_ddi()
        patched_i_device_mounter.unmount_image.assert_called_once()


@pytest.mark.parametrize("paired,developer_mode_enabled", [(True, True)])
class TestIDeviceRSD:
    @pytest.mark.parametrize("product_version", ["17.0", "17.4", "18.0"])
    @pytest.mark.parametrize("ddi_mounted", [True])
    async def test_establish_trusted_channel(
        self,
        i_device_mocked_lockdown,
        ddi_mounted,
        patched_i_device_mounter,
        fake_tunnel_result,
        mocked_client_socket,
        tunnel_client_with_mocked_socket,
        product_version,
    ):
        """
        GIVEN: An IDevice instance that is ready to establish a trusted channel.

        WHEN: establish_trusted_channel is called

        THEN: The `TunnelClient.start_tunnel` method should be called.
        """
        with patch(
            "core.device.i_device.RemoteServiceDiscoveryService.connect"
        ) as mock_rsd_connect:
            with patch("core.device.i_device.get_tunnel_client") as mock_client:
                mock_client.return_value.__enter__.return_value = (
                    tunnel_client_with_mocked_socket
                )
                mocked_client_socket.receive.return_value = SuccessResponse(
                    data=fake_tunnel_result.model_dump(mode="json")
                )
                patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted

                await i_device_mocked_lockdown.establish_trusted_channel()

                assert i_device_mocked_lockdown.rsd.service.address == (
                    str(fake_tunnel_result.address),
                    fake_tunnel_result.port,
                )

                mock_rsd_connect.assert_awaited_once()

    @pytest.mark.parametrize("product_version", ["16.0"])
    @pytest.mark.parametrize("ddi_mounted", [True])
    async def test_establish_trusted_channel_not_supported(
        self,
        i_device_mocked_lockdown,
        product_version,
        ddi_mounted,
        patched_i_device_mounter,
    ):
        """
        GIVEN: An IDevice instance with product version < 17.0.

        WHEN: establish_trusted_channel is called

        THEN: A `RsdNotSupported` exception should be raised.
        """
        patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted

        with pytest.raises(RsdNotSupported):
            await i_device_mocked_lockdown.establish_trusted_channel()

    @pytest.mark.parametrize("product_version", ["17.0"])
    def test_rsd_property_getter_none(self, i_device_mocked_lockdown, product_version):
        """
        GIVEN: An IDevice instance.
        AND: The `rsd` property is not set.

        WHEN: The `rsd` property is accessed.

        THEN: The `rsd` property should return None.
        """
        assert i_device_mocked_lockdown.rsd is None

    @pytest.mark.parametrize("product_version", ["16.0"])
    def test_rsd_property_getter_not_supported(
        self, i_device_mocked_lockdown, product_version
    ):
        """
        GIVEN: An IDevice instance.
        AND: The product version is < 17.0.

        WHEN: The `rsd` property is accessed.

        THEN: The `RsdNotSupported` exception should be raised.
        """
        with pytest.raises(RsdNotSupported):
            _ = i_device_mocked_lockdown.rsd


class TestIDeviceDVT:
    @pytest.mark.parametrize(
        "paired,product_version",
        [
            (False, "15.0"),
            (False, "16.0"),
            (False, "17.0"),
            (False, "18.0"),
        ],
    )
    @pytest.mark.parametrize("developer_mode_enabled", [None])
    def test_check_dvt_ready_not_paired(
        self, i_device_mocked_lockdown, paired, product_version, developer_mode_enabled
    ):
        """
        GIVEN: An IDevice instance that is not paired.

        WHEN: check_dvt_ready is called.

        THEN: A `DeviceNotReadyForDvt` exception should be raised with `DeviceNotPaired` as the cause.
        """
        with pytest.raises(DeviceNotReadyForDvt) as e:
            i_device_mocked_lockdown.check_dvt_ready()
        assert isinstance(e.value.__cause__, DeviceNotPaired)

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,",
        [
            (True, "15.0", None),
            (True, "16.0", False),
            (True, "17.0", False),
            (True, "18.0", False),
        ],
    )
    def test_check_dvt_ready_developer_mode_not_enabled(
        self,
        i_device_mocked_lockdown,
        paired,
        product_version,
        developer_mode_enabled,
        patched_i_device_mounter,
    ):
        """
        GIVEN: An IDevice instance that is paired but developer mode is not enabled or not supported.
        AND: The Developer Disk Image is not mounted.

        WHEN: check_dvt_ready is called.

        THEN: A `DeviceNotReadyForDvt` exception should be raised with `DeveloperModeNotEnabled` as the cause.
        OR: A `DeviceNotReadyForDvt` exception should be raised with the `DdiNotMounted` when the developer mode is not
        supported.
        """
        patched_i_device_mounter.is_image_mounted.return_value = False

        if i_device_mocked_lockdown.requires_developer_mode:
            with pytest.raises(DeviceNotReadyForDvt) as e:
                i_device_mocked_lockdown.check_dvt_ready()
            assert isinstance(e.value.__cause__, DeveloperModeNotEnabled)
        else:
            # If the device does not require developer mode to be enabled, it should still raise an exception as the
            # dd image is not mounted in this case.
            with pytest.raises(DeviceNotReadyForDvt) as e:
                i_device_mocked_lockdown.check_dvt_ready()
            assert isinstance(e.value.__cause__, DdiNotMounted)

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,ddi_mounted",
        [
            (True, "15.0", None, False),
            (True, "16.0", True, False),
            (True, "17.0", True, False),
            (True, "18.0", True, False),
        ],
    )
    def test_check_dvt_ready_ddi_not_mounted(
        self,
        i_device_mocked_lockdown,
        paired,
        product_version,
        developer_mode_enabled,
        ddi_mounted,
        patched_i_device_mounter,
    ):
        """
        GIVEN: An IDevice instance that is paired, has developer mode enabled, but the Developer Disk Image is not
        mounted.

        WHEN: check_dvt_ready is called.

        THEN: A `DeviceNotReadyForDvt` exception should be raised with `DdiNotMounted` as the cause.
        """
        patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted

        with pytest.raises(DeviceNotReadyForDvt) as e:
            i_device_mocked_lockdown.check_dvt_ready()
        assert isinstance(e.value.__cause__, DdiNotMounted)

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,ddi_mounted,rsd_connected",
        [
            (True, "15.0", None, True, False),
            (True, "16.0", True, True, False),
            (True, "17.0", True, True, False),
            (True, "18.0", True, True, False),
        ],
    )
    def test_check_dvt_ready_rsd_not_set(
        self,
        i_device_mocked_lockdown,
        paired,
        product_version,
        developer_mode_enabled,
        ddi_mounted,
        rsd_connected,
    ):
        """
        GIVEN: An IDevice instance that is paired, has developer mode enabled, the Developer Disk Image is mounted, but
        the Remote Service Discovery is not connected.

        WHEN: check_dvt_ready is called.

        THEN: A `DeviceNotReadyForDvt` exception should be raised with `RsdNotSet` as the cause.
        """
        if i_device_mocked_lockdown.requires_tunnel_for_developer_tools:
            with pytest.raises(DeviceNotReadyForDvt) as e:
                i_device_mocked_lockdown.check_dvt_ready()
            assert isinstance(e.value.__cause__, RsdNotConnected)
        else:
            # If the device does not require RSD, the check should pass at this point.
            i_device_mocked_lockdown.check_dvt_ready()


class TestIDeviceProperties:
    def test_udid_property(self):
        """
        GIVEN: a lockdown client with an udid
        AND: an IDevice instance with the lockdown client

        WHEN: udid is called

        THEN: the udid of the lockdown client should be returned
        """
        udid = "1234567890"
        lockdown_service = MagicMock(spec=UsbmuxLockdownClient, udid=udid)
        i_device = IDevice(lockdown_service)
        assert i_device.udid == udid

    def test_udid_property_when_rsd(self):
        """
        GIVEN: a lockdown client with an udid
        AND: an IDevice instance with the lockdown client
        AND: an RSD service with a different udid assigned to the IDevice instance

        WHEN: udid is called

        THEN: the udid of the RSD service should be returned
        """
        udid = "1234567890"
        udid2 = "0987654321"
        lockdown_service = MagicMock(spec=UsbmuxLockdownClient, udid=udid)
        i_device = IDevice(lockdown_service)
        i_device._rsd = MagicMock(spec=RemoteServiceDiscoveryService, udid=udid2)
        assert i_device.udid == udid2

    @pytest.mark.parametrize(
        "paired,product_version,developer_mode_enabled,ddi_mounted,rsd_connected",
        [
            (False, "15.0", None, False, None),
            (True, "15.0", None, False, None),
            (True, "15.0", None, False, None),
            (False, "16.0", False, False, None),
            (True, "16.0", False, False, None),
            (True, "16.0", True, False, None),
            (True, "16.0", True, True, None),
            (False, "17.0", False, False, False),
            (True, "17.0", True, False, False),
            (True, "17.0", True, True, False),
            (True, "17.0", True, True, True),
        ],
    )
    def test_status_property(
        self,
        i_device_mocked_lockdown,
        patched_i_device_mounter,
        paired,
        product_version,
        developer_mode_enabled,
        ddi_mounted,
        rsd_connected,
    ):
        """
        GIVEN: a lockdown client with a certain state

        WHEN: status is called

        THEN: the correct status of the device should be returned
        """
        patched_i_device_mounter.is_image_mounted.return_value = ddi_mounted
        if rsd_connected:
            i_device_mocked_lockdown._rsd = MagicMock(
                spec=RemoteServiceDiscoveryService
            )

        result = i_device_mocked_lockdown.status

        assert result == IDeviceStatus(
            paired=paired,
            ddi_mounted=ddi_mounted,
            developer_mode_enabled=developer_mode_enabled,
            tunnel_connected=rsd_connected,
        )

    def test_info_property(self):
        """
        GIVEN: a lockdown client with a short info

        WHEN: info is called

        THEN: the parsed info of the lockdown client should be returned
        """
        short_info = {
            "BuildVersion": "22B91",
            "ConnectionType": "USB",
            "DeviceClass": "iPhone",
            "DeviceName": "iPhone",
            "Identifier": "00000000-0000000000000000",
            "ProductType": "iPhone14,4",
            "ProductVersion": "18.1.1",
            "UniqueDeviceID": "00000000-0000000000000000",
        }  # Real data from an iPhone

        lockdown_service = MagicMock(spec=UsbmuxLockdownClient, short_info=short_info)
        i_device = IDevice(lockdown_service)

        info = i_device.info

        assert info.build_version == short_info["BuildVersion"]
        assert info.device_class == short_info["DeviceClass"]
        assert info.device_name == short_info["DeviceName"]
        assert info.product_version == short_info["ProductVersion"]
        assert info.product_type == short_info["ProductType"]

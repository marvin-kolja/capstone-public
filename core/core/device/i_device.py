import asyncio
import logging
from datetime import timedelta
from typing import Optional

from packaging.version import Version
from pymobiledevice3.lockdown import UsbmuxLockdownClient, LockdownClient
from pymobiledevice3.lockdown_service_provider import LockdownServiceProvider
from pymobiledevice3.remote.remote_service_discovery import (
    RemoteServiceDiscoveryService,
)
from pymobiledevice3 import exceptions as pmd3_exceptions
from pymobiledevice3.services.amfi import AmfiService
from pymobiledevice3.services.mobile_image_mounter import (
    MobileImageMounterService,
    DeveloperDiskImageMounter,
    PersonalizedImageMounter,
    auto_mount,
)

from core.exceptions import i_device as device_exceptions
from core.tunnel.client import get_tunnel_client

logger = logging.getLogger(__name__)


class IDevice:
    """
    Wrapper for lockdown client and remote service discovery service.
    """

    def __init__(self, lockdown_client: UsbmuxLockdownClient):
        logger.debug(
            f"Initializing IDevice with lockdown client {type(lockdown_client).__name__}"
        )
        self._lockdown_client = lockdown_client
        self._rsd: Optional[RemoteServiceDiscoveryService] = None

    @property
    def lockdown_service(self) -> LockdownServiceProvider:
        """
        Returns either the `rsd` or `usbmux_lockdown` property.

        If the `rsd` property is not `None`, it is favored over the `usbmux_lockdown` property.

        Note: The `rsd` property may only be available for devices with iOS 17.0 or later. Refer to the `rsd` property
        documentation for more information.
        """
        if self._rsd is not None:
            logger.debug(f"Returning rsd as lockdown service")
            return self._rsd
        logger.debug(
            f"Returning {type(self._lockdown_client).__name__} as lockdown service"
        )
        return self._lockdown_client

    @property
    def lockdown_client(self) -> LockdownClient:
        """
        Returns the `LockdownClient` instance.

        If the device is running iOS 17.0 or later, the `rsd` property should be used instead.
        """
        return self._lockdown_client

    @property
    def rsd(self) -> Optional[RemoteServiceDiscoveryService]:
        """
        As of iOS 17.0 Apple requires a secure tunnel to access developer services using the `RemoteXPC` protocol.

        For more information read:
        https://github.com/doronz88/pymobiledevice3/blob/master/misc/understanding_idevice_protocol_layers.md#remotexpc

        The property is `None` if `establish_trusted_channel` has never been called.

        :raises RsdNotSupported: **Only available for >= iOS 17.0**
        """
        if not self.requires_tunnel_for_developer_tools:
            logger.error(
                f"Tried to get rsd on an unsupported device version {self.lockdown_client.product_version} < 17.0"
            )
            raise device_exceptions.RsdNotSupported()
        return self._rsd

    @property
    def requires_tunnel_for_developer_tools(self) -> bool:
        """
        Check if the device OS requires a tunnel to access developer services.
        """
        return Version(self.lockdown_client.product_version) >= Version("17.0")

    @property
    def requires_developer_mode(self) -> bool:
        """
        Check if the device OS requires developer mode to be enabled in order to mount DDI.
        """
        return Version(self.lockdown_client.product_version) >= Version("16.0")

    @property
    def paired(self) -> bool:
        return self.lockdown_client.paired

    def check_paired(self):
        """
        :raises DeviceNotPaired:
        """
        if not self.paired:
            raise device_exceptions.DeviceNotPaired

    def pair(self):
        """
        Pair the device

        :raises UserDeniedPairing:
        :raises PasswordRequireError:
        :raises PairingError:
        """
        try:
            logger.debug(f"Pairing device {self.lockdown_client.udid}")
            self._lockdown_client.pair()
        except pmd3_exceptions.UserDeniedPairingError:
            raise device_exceptions.UserDeniedPairing
        except pmd3_exceptions.PasswordRequiredError:
            raise device_exceptions.PasswordRequired
        except pmd3_exceptions.PairingError as e:
            raise device_exceptions.PairingError from e
        except Exception as e:
            raise device_exceptions.PairingError from e

    def unpair(self):
        """
        Unpair the device

        :raises DeviceNotPaired:
        :raises PairingError:
        """
        if not self.paired:
            raise device_exceptions.DeviceNotPaired
        try:
            logger.debug(f"Unpairing device {self.lockdown_client.udid}")
            self._lockdown_client.unpair()
        except Exception as e:
            raise device_exceptions.PairingError from e

    @property
    def developer_mode_enabled(self) -> bool:
        """
        **Only available for >= iOS 16**

        :raises DeveloperModeNotSupported:
        :raises DeveloperModeError:

        :raises DeviceNotPaired:
        """
        if not self.requires_developer_mode:
            logger.error(
                f"Tried to get developer for an unsupported device version {self.lockdown_client.product_version} < 16.0"
            )
            raise device_exceptions.DeveloperModeNotSupported
        self.check_paired()
        try:
            return self._lockdown_client.developer_mode_status
        except Exception as e:
            raise device_exceptions.DeveloperModeError from e

    def check_developer_mode_enabled(self):
        """
        :raises DeveloperModeNotEnabled:

        :raises DeveloperModeNotSupported:
        :raises DeveloperModeError:

        :raises DeviceNotPaired:
        """
        if not self.developer_mode_enabled:
            raise device_exceptions.DeveloperModeNotEnabled

    def enable_developer_mode(self):
        """
        Enable Developer Mode on the device

        **Only available for >= iOS 16**

        :raises DeveloperModeNotSupported:
        :raises DeveloperModeAlreadyEnabled:

        :raises DeviceHasPasscodeSet:

        :raises DeviceNotPaired:
        """
        if self.developer_mode_enabled:
            raise device_exceptions.DeveloperModeAlreadyEnabled
        try:
            logger.debug(
                f"Enabling Developer Mode for device {self.lockdown_client.udid}"
            )
            AmfiService(self._lockdown_client).enable_developer_mode()
        except pmd3_exceptions.DeviceHasPasscodeSetError as e:
            raise device_exceptions.DeviceHasPasscodeSet from e
        except Exception as e:
            raise device_exceptions.DeveloperModeError from e

    @property
    def _mounter(self) -> MobileImageMounterService:
        if Version(self.lockdown_service.product_version) < Version("17.0"):
            return DeveloperDiskImageMounter(self.lockdown_service)
        return PersonalizedImageMounter(self.lockdown_service)

    @property
    def ddi_mounted(self) -> bool:
        """
        :raises DeveloperModeNotEnabled:
        :raises DeveloperModeError:

        :raises DeviceNotPaired:
        """
        try:
            self.check_developer_mode_enabled()
        except device_exceptions.DeveloperModeNotSupported:
            self.check_paired()

        return self._mounter.is_image_mounted(self._mounter.IMAGE_TYPE)

    def check_ddi_mounted(self):
        """
        :raises DdiNotMounted:

        :raises DeveloperModeNotEnabled:
        :raises DeveloperModeError:

        :raises DeviceNotPaired:
        """
        if not self.ddi_mounted:
            raise device_exceptions.DdiNotMounted

    async def mount_ddi(self):
        """
        Mount Developer Disk Image

        :raises DdiMountingError:

        :raises DeveloperModeNotEnabled:
        :raises DeveloperModeError:

        :raises DeviceNotPaired:
        """
        if self.ddi_mounted:
            raise device_exceptions.DdiAlreadyMounted

        try:
            logger.debug(
                f"Mounting Developer Disk Image for device {self.lockdown_client.udid}"
            )
            await auto_mount(self.lockdown_service)
        except Exception as e:
            raise device_exceptions.DdiMountingError from e

    def unmount_ddi(self):
        """
        Unmount Developer Disk Image

        :raises DdiNotMounted:
        :raises DdiMountingError:

        :raises DeveloperModeNotEnabled:

        :raises DeviceNotPaired:
        """
        self.check_ddi_mounted()

        try:
            logger.debug(
                f"Unmounting Developer Disk Image for device {self.lockdown_client.udid}"
            )
            self._mounter.unmount_image(self._mounter.IMAGE_TYPE)
        except Exception as e:
            raise device_exceptions.DdiMountingError from e

    async def establish_trusted_channel(self):
        """
        Creates a `RemoteServiceDiscoveryService` for the device by establishing a tunnel using `TunnelClient`. This
        communicates with the `TunnelServer` which is required to run.

        When the tunnel already exists it will reuse the existing tunnel.

        For detailed implementation on how the communication works and tunnels are managed, refer to
        :mod:`core.tunnel`.

        The method sets the `rsd` property to the created `RemoteServiceDiscoveryService`.

        **Only available for >= iOS 17.0**

        :raises DeviceNotPaired:
        :raises DeveloperModeNotEnabled:
        :raises DdiNotMounted:
        :raises RsdNotSupported:
        :raises asyncio.TimeoutError:
        :raises TunnelAlreadyExistsError:
        :raises TunnelCreationFailure:
        """
        if not self.requires_tunnel_for_developer_tools:
            logger.error(
                f"Tried to establish trusted tunnel for an unsupported device version {self.lockdown_client.product_version} < 17.0"
            )
            raise device_exceptions.RsdNotSupported()

        self.check_ddi_mounted()

        with get_tunnel_client(port=49151, timeout=timedelta(seconds=10)) as client:
            try:
                logger.debug(
                    f"Checking if tunnel exist for device {self.lockdown_client.udid}"
                )
                tunnel = await client.get_tunnel(self.lockdown_service.udid)

                if tunnel is None:
                    logger.debug(
                        f"Tunnel does not exist for device {self.lockdown_client.udid}, trying to start it"
                    )
                    tunnel = await client.start_tunnel(self.lockdown_service.udid)
                logger.debug(
                    f"Got tunnel {tunnel} for device {self.lockdown_client.udid}"
                )
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                raise device_exceptions.TunnelCreationFailure from e

        if tunnel is None:
            raise device_exceptions.TunnelCreationFailure("Returned tunnel is None")

        logger.debug(f"Creating rsd with tunnel for device {self.lockdown_client.udid}")
        rsd = RemoteServiceDiscoveryService((str(tunnel.address), tunnel.port))
        logger.debug(
            f"Connecting to rsd service for device {self.lockdown_client.udid}"
        )
        await rsd.connect()

        self._rsd = rsd

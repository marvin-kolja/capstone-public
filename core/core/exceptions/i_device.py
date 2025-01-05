from core.exceptions import CoreException


class PairingError(CoreException):
    """Errors related to pairing with the device"""

    pass


class UserDeniedPairing(PairingError):
    """Raised when pairing fails due to user denying the pairing request"""

    pass


class DeviceNotPaired(PairingError):
    """Raised when the device is not paired"""

    pass


class PasswordRequired(PairingError):
    """Raised when a password is required to pair with the device"""

    pass


class DeveloperModeError(CoreException):
    """Errors related to enabling developer mode"""

    pass


class DeveloperModeNotSupported(DeveloperModeError):
    """Raised when developer mode is not supported on the device"""

    pass


class DeveloperModeAlreadyEnabled(DeveloperModeError):
    """Raised when developer mode is already enabled on the device"""

    pass


class DeveloperModeNotEnabled(DeveloperModeError):
    """Raised when developer mode is not enabled on the device"""

    pass


class DeviceHasPasscodeSet(DeveloperModeError):
    """We can't enable developer mode if the device has a passcode set"""

    pass


class DdiMountingError(CoreException):
    """Errors related to mounting Developer Disk Image"""

    pass


class DdiNotMounted(DdiMountingError):
    """Raised when Developer Disk Image is not mounted"""

    pass


class DdiAlreadyMounted(DdiMountingError):
    """Raised when Developer Disk Image is already mounted"""

    pass


class RsdNotSupported(CoreException):
    """Raised when the device is not running iOS 17 or later"""

    def __init__(self):
        super().__init__("RSD is only supported on iOS 17 and later")


class TunnelCreationFailure(CoreException):
    """Unable to start a tunnel to the device"""

    pass


class AppInstallError(CoreException):
    """Error when unable to install app"""

    pass


class AppUninstallError(CoreException):
    """Errors related to uninstalling the device"""

    pass


class AppListError(CoreException):
    """Errors related to listing installed apps"""

    pass

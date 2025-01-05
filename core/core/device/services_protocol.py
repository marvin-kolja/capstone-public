from typing import Protocol


class ServicesProtocol(Protocol):
    def install_app(self, app_path: str):
        """
        Install an app on the device using the app path.
        """
        ...

    def uninstall_app(self, bundle_id: str):
        """
        Uninstall an app from the device using the bundle id
        """
        ...

    def list_installed_apps(self) -> list:
        """
        List all installed apps on the device
        """
        ...

    def launch_app(self, bundle_id: str):
        """
        Launch an app on the device using the bundle id
        """
        ...

    def terminate_app(self, bundle_id: str):
        """
        Terminate an app on the device using the bundle id
        """
        ...

    def pid_for_app(self, bundle_id: str) -> int:
        """
        Returns the process identifier (PID) for an app running on the device
        """
        ...

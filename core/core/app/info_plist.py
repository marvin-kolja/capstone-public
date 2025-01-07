from typing import Optional

from pydantic import BaseModel


class InfoPlist(BaseModel):
    """
    Please refer to https://developer.apple.com/documentation/bundleresources/information-property-list for information
    about the fields used here. Specifically, the sections in 'Core settings' -> 'Bundle Configuration'.

    The fields here are not exhaustive and only include the fields that are relevant to this project.
    """

    CFBundlePackageType: str
    """
    The type of bundle.
    Name: Bundle OS Type code
    """

    CFBundleIdentifier: str
    """
    A unique identifier for a bundle.
    Name: Bundle identifier
    """

    CFBundleName: str
    """
    A user-visible short name for the bundle.
    Name: Bundle name
    """

    CFBundleDisplayName: Optional[str] = None
    """
    The user-visible name for the bundle, used by Siri and visible on the iOS Home screen.
    Name: Bundle display name
    """

    MinimumOSVersion: str
    """
    The minimum version of the operating system required for the app to run in iOS, iPadOS, tvOS, and watchOS.    
    """

    LSRequiresIPhoneOS: Optional[bool] = None
    """
    A Boolean value indicating whether the app must run in iOS.
    Name: Application requires iPhone environment
    """

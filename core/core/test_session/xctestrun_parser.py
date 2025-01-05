import plistlib

from pydantic import BaseModel
from typing import Optional, BinaryIO, Any

from core.exceptions.common import InvalidFileContent


class ContainerInfo(BaseModel):
    """
    Please refer to https://keith.github
    """

    ContainerName: str
    SchemeName: str


class XcTestTarget(BaseModel):
    """
    Please refer to https://keith.github.io/xcode-man-pages/xcodebuild.xctestrun.5.html#TestTargets for
    information about the fields.
    """

    BlueprintName: str
    TestBundlePath: str
    TestHostPath: str
    UITargetAppPath: Optional[str] = None
    EnvironmentVariables: dict[str, str] = dict
    CommandLineArguments: list[str] = list
    UITargetAppEnvironmentVariables: Optional[dict[str, str]] = None
    UITargetAppCommandLineArguments: Optional[list[str]] = None
    BaselinePath: Optional[str] = None
    TreatMissingBaselinesAsFailures: Optional[bool] = None
    SkipTestIdentifiers: Optional[list[str]] = None
    OnlyTestIdentifiers: Optional[list[str]] = None
    UITargetAppMainThreadCheckerEnabled: Optional[bool] = None
    GatherLocalizableStringsData: Optional[bool] = None
    DependentProductPaths: list[str] = list
    ProductModuleName: Optional[str] = None
    SystemAttachmentLifetime: Optional[str] = None
    UserAttachmentLifetime: Optional[str] = None
    ParallelizationEnabled: bool = False
    TestExecutionOrdering: Optional[str] = None
    TestLanguage: Optional[str] = None
    TestRegion: Optional[str] = None
    UseDestinationArtifacts: Optional[bool] = None
    TestHostBundleIdentifier: Optional[str] = None
    TestBundleDestinationRelativePath: Optional[str] = None
    PreferredScreenCaptureFormat: Optional[str] = None
    TestingEnvironmentVariables: dict[str, str] = dict


class XcTestConfiguration(BaseModel):
    """
    Please refer to https://keith.github.io/xcode-man-pages/xcodebuild.xctestrun.5.html#TEST_CONFIGURATIONS_SECTION for
    information about the fields.
    """

    Name: str
    TestTargets: list[XcTestTarget]


class XcTestPlan(BaseModel):
    """
    Please refer to https://keith.github.io/xcode-man-pages/xcodebuild.xctestrun.5.html#TEST_PLAN_SECTION for
    information about the fields.
    """

    IsDefault: bool
    Name: str


class XcTestrunMetadata(BaseModel):
    """
    Please refer to https://keith.github.io/xcode-man-pages/xcodebuild.xctestrun.5.html#METADATA_SECTION for information
    about the fields.
    """

    FormatVersion: int


class Xctestrun(BaseModel):
    """
    Defines the structure of the xctestrun file when parsed to a dictionary.

    Please refer to https://keith.github.io/xcode-man-pages/xcodebuild.xctestrun.5.html for information about the
    fields.
    """

    ContainerInfo: ContainerInfo
    TestConfigurations: list[XcTestConfiguration]
    TestPlan: XcTestPlan
    __xctestrun_metadata__: XcTestrunMetadata


def read_xctestrun_file(path: str) -> BinaryIO:
    """
    Read the content of the xctestrun file as binary.

    :param path: The path to the xctestrun file.

    :return: The binary content of the xctestrun file.

    :raises: `FileNotFoundError` when the file does not exist.
    """
    return open(path, "rb")


def parse_xctestrun_content(content: BinaryIO) -> Xctestrun:
    """
    Parse binary content of xctestrun file and return a Xctestrun instance.

    :param content: The binary content of the xctestrun file.

    :return: A Xctestrun instance.

    :raises: `InvalidFileContent` when unable to read the content.
    :raises: `pydantic.ValidationError` when unable to validate the content.
    """
    try:
        xctestrun_dict: dict[str, Any] = plistlib.load(content)
    except Exception as e:
        raise InvalidFileContent from e

    return Xctestrun(**xctestrun_dict)

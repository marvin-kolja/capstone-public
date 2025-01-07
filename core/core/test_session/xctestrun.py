from pydantic import BaseModel, field_validator
from typing import Optional


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

    @field_validator("TestHostPath", "UITargetAppPath", mode="before")
    def validate_test_host_and_ui_target_app_paths(cls, value):
        """
        Make sure that the path do not contain __TESTROOT__ placeholder.
        """
        if value is None:
            return value
        if "__TESTROOT__" in value:
            raise ValueError(f"Path '{value}' contains the '__TESTROOT__' placeholder")
        return value


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

    def extract_test_configuration_with_name(self, name: str) -> XcTestConfiguration:
        """
        Extract the test configuration from the xctestrun file that matches the provided name.

        :param name: The name of the test configuration to extract.
        :return: The test configuration that matches the provided name.
        :raises ValueError: when the test configuration with the provided name is not found.
        """
        for configuration in self.TestConfigurations:
            if configuration.Name == name:
                return configuration

        raise ValueError(f"Test configuration '{name}' not found in xctestrun")

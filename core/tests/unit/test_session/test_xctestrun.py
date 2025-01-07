import pytest

from core.test_session.xctestrun import (
    Xctestrun,
    ContainerInfo,
    XcTestPlan,
    XcTestrunMetadata,
    XcTestConfiguration,
)


class TestXctestrun:
    def test_extract_test_configuration_with_name_not_found(self):
        """
        GIVEN a Xctestrun object

        WHEN extract_test_configuration_with_name is called with a name that is not in the xctestrun

        THEN a ValueError should be raised
        """
        xctestrun = Xctestrun(
            ContainerInfo=ContainerInfo(
                ContainerName="name",
                SchemeName="name",
            ),
            TestConfigurations=[XcTestConfiguration(Name="name", TestTargets=[])],
            TestPlan=XcTestPlan(IsDefault=True, Name="name"),
            __xctestrun_metadata__=XcTestrunMetadata(FormatVersion=1),
        )

        with pytest.raises(ValueError):
            xctestrun.extract_test_configuration_with_name("not_name")

    def test_extract_test_configuration_with_name_found(self):
        """
        GIVEN a Xctestrun object

        WHEN extract_test_configuration_with_name is called with a name that is in the xctestrun

        THEN the test configuration should be returned
        """
        test_configuration = XcTestConfiguration(Name="name", TestTargets=[])
        xctestrun = Xctestrun(
            ContainerInfo=ContainerInfo(
                ContainerName="name",
                SchemeName="name",
            ),
            TestConfigurations=[test_configuration],
            TestPlan=XcTestPlan(IsDefault=True, Name="name"),
            __xctestrun_metadata__=XcTestrunMetadata(FormatVersion=1),
        )

        returned_configuration = xctestrun.extract_test_configuration_with_name("name")

        assert returned_configuration == test_configuration

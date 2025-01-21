import pytest

from core.device.i_device_manager import IDeviceManager


@pytest.mark.skip(
    reason="""
This test is flaky.

It seems that mounting and unmounting the ddi multiple times makes the device not available to xcode immediately after.
This results in other tests to fail that use tools such as xcodebuild. As the mounting functionality is either way
coming from another library, we can skip this test.
"""
)
class TestIDevice:
    @pytest.mark.real_device
    async def test_mounting_process(self, device_udid):
        """
        GIVEN: a real device

        WHEN: The ddi is already mounted, unmount it
        AND: Mount the ddi
        AND: Unmount the ddi

        THEN: The ddi should be mounted and unmounted successfully
        """
        device = IDeviceManager().get_device(udid=device_udid)

        if device.ddi_mounted:
            device.unmount_ddi()
        assert not device.ddi_mounted

        await device.mount_ddi()
        assert device.ddi_mounted

        device.unmount_ddi()
        assert not device.ddi_mounted

        await device.mount_ddi()  # Mount it again to avoid errors in other tests
        assert device.ddi_mounted

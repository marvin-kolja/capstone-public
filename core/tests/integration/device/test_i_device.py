import pytest

from core.device.i_device_manager import IDeviceManager


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
            await device.unmount_ddi()
        assert not device.ddi_mounted

        await device.mount_ddi()
        assert device.ddi_mounted

        await device.unmount_ddi()
        assert not device.ddi_mounted

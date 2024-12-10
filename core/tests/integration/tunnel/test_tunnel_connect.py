import pytest

from core.exceptions.tunnel_connect import TunnelAlreadyExistsError


@pytest.mark.requires_sudo
@pytest.mark.real_device
class TestTunnelConnect:
    """
    Test cases for TunnelConnect class
    """

    async def test_start_tunnel(self, tunnel_connect, device_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A real UDID

        WHEN: start_tunnel is called

        THEN: The function should return a tunnel result
        """
        tunnel_result = await tunnel_connect.start_tunnel(device_udid)

        assert tunnel_result is not None

    async def test_start_tunnel_already_started(self, tunnel_connect, device_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A real UDID

        WHEN: start_tunnel is called twice with the same UDID

        THEN: The function should raise a TunnelAlreadyExistsError
        """

        await tunnel_connect.start_tunnel(device_udid)

        with pytest.raises(TunnelAlreadyExistsError):
            await tunnel_connect.start_tunnel(device_udid)

    async def test_stop_tunnel(self, tunnel_connect, device_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A real UDID

        WHEN: stop_tunnel is called

        THEN: The tunnel task should be removed from the tunnel tasks
        """
        await tunnel_connect.start_tunnel(device_udid)

        await tunnel_connect.stop_tunnel(device_udid)

        assert device_udid not in tunnel_connect._tunnel_manager.tunnel_tasks

    async def test_get_tunnel(self, tunnel_connect, device_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A started mocked tunnel task

        WHEN: get_tunnel is called

        THEN: The tunnel result should match the started tunnel result
        """
        started_tunnel = await tunnel_connect.start_tunnel(device_udid)

        tunnel_result = tunnel_connect.get_tunnel(device_udid)

        assert tunnel_result is not None
        assert tunnel_result == started_tunnel

    async def test_close(self, tunnel_connect, device_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A real UDID

        WHEN: close is called

        THEN: The tunnel tasks should be empty
        """
        await tunnel_connect.start_tunnel(device_udid)

        await tunnel_connect.close()

        assert not tunnel_connect._tunnel_manager.tunnel_tasks


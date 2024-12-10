import pytest

from core.exceptions.tunnel_connect import TunnelAlreadyExistsError


class TestTunnelConnect:
    """
    Test cases for TunnelConnect class
    """

    async def test_start_tunnel(self, tunnel_connect, fake_udid, mock_tunnel_connect__start_usbmux_tcp_tunnel_task,
                                mocked_pymd3_tunnel_result):
        """
        GIVEN: A TunnelConnect instance
        AND: A simulated UDID
        AND: A mocked tunnel task

        WHEN: start_tunnel is called

        THEN: The function should return a tunnel result
        AND: The tunnel task should be added to the tunnel tasks of TunneldCore
        AND: The tunnel task should not be done
        AND: The tunnel should be the mocked tunnel
        """

        tunnel_result = await tunnel_connect.start_tunnel(fake_udid)

        assert tunnel_result is not None
        assert tunnel_result.port == mocked_pymd3_tunnel_result.port
        assert str(tunnel_result.address) == mocked_pymd3_tunnel_result.address
        tunnel_task = tunnel_connect._tunnel_manager.tunnel_tasks[fake_udid]
        assert not tunnel_task.task.done()
        assert tunnel_task.tunnel == mocked_pymd3_tunnel_result

    async def test_start_tunnel_already_started(self, tunnel_connect, fake_udid,
                                                mock_tunnel_connect__start_usbmux_tcp_tunnel_task):
        """
        GIVEN: A TunnelConnect instance
        AND: A simulated UDID
        AND: A mocked tunnel task

        WHEN: start_tunnel is called twice with the same UDID

        THEN: The function should raise a TunnelAlreadyExistsError
        """
        await tunnel_connect.start_tunnel(fake_udid)

        with pytest.raises(TunnelAlreadyExistsError):
            await tunnel_connect.start_tunnel(fake_udid)

    async def test_stop_tunnel(self, tunnel_connect, fake_udid, mock_tunnel_connect__start_usbmux_tcp_tunnel_task):
        """
        GIVEN: A TunnelConnect instance
        AND: A started mocked tunnel task

        WHEN: stop_tunnel is called

        THEN: The tunnel task should be removed from the tunnel tasks
        """
        await tunnel_connect.start_tunnel(fake_udid)

        await tunnel_connect.stop_tunnel(fake_udid)

        assert fake_udid not in tunnel_connect._tunnel_manager.tunnel_tasks

    async def test_stop_tunnel_not_found(self, tunnel_connect, fake_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A UDID that is not in the tunnel tasks

        WHEN: stop_tunnel is called

        THEN: The function should not raise an error
        """
        await tunnel_connect.stop_tunnel(fake_udid)

    async def test_get_tunnel(self, tunnel_connect, fake_udid, mock_tunnel_connect__start_usbmux_tcp_tunnel_task):
        """
        GIVEN: A TunnelConnect instance
        AND: A started mocked tunnel task

        WHEN: get_tunnel is called

        THEN: The tunnel result should match the started tunnel result
        """
        started_tunnel = await tunnel_connect.start_tunnel(fake_udid)

        tunnel_result = tunnel_connect.get_tunnel(fake_udid)

        assert tunnel_result is not None
        assert tunnel_result == started_tunnel

    def test_get_tunnel_not_found(self, tunnel_connect, fake_udid):
        """
        GIVEN: A TunnelConnect instance
        AND: A UDID that is not in the tunnel tasks

        WHEN: get_tunnel is called

        THEN: None should be returned
        """
        tunnel_result = tunnel_connect.get_tunnel(fake_udid)

        assert tunnel_result is None

    async def test_close(self, tunnel_connect, fake_udid, mock_tunnel_connect__start_usbmux_tcp_tunnel_task):
        """
        GIVEN: A TunnelConnect instance
        AND: A started mocked tunnel task

        WHEN: close is called

        THEN: The tunnel tasks should be empty
        """
        await tunnel_connect.start_tunnel(fake_udid)

        await tunnel_connect.close()

        assert not tunnel_connect._tunnel_manager.tunnel_tasks

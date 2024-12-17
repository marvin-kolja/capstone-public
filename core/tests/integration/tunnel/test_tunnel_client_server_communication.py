import pytest
from pymobiledevice3.exceptions import DeviceNotFoundError
from pymobiledevice3.remote.common import TunnelProtocol

from core.exceptions.tunnel_connect import TunnelAlreadyExistsError
from core.tunnel.server_exceptions import MalformedRequestError, NotFoundError


class TestTunnelClientServerCommunication:
    """
    Test tunnel client and server integration.

    This mainly tests if the client gets the correct response from the server.
    """

    @pytest.mark.asyncio
    async def test_server_not_running(self, tunnel_client):
        """
        GIVEN: A TunnelClient instance
        AND: The server is not running

        WHEN: `TunnelClient.start_tunnel` is called

        THEN: The client should raise a TimeoutError
        """
        with pytest.raises(TimeoutError):
            await tunnel_client.start_tunnel('udid')

    @pytest.mark.asyncio
    @pytest.mark.real_device
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_malformed_requests(self, server, tunnel_client, device_udid):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance

        WHEN: Malformed requests are sent to the server

        THEN: The server should raise an MalformedRequestError
        """
        with pytest.raises(MalformedRequestError):
            await tunnel_client._call_server('start_tunnel', udid=100)

        with pytest.raises(MalformedRequestError):
            await tunnel_client._call_server('start_tunnel', udid=device_udid, invalid_key='invalid_value')

    @pytest.mark.asyncio
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_calling_invalid_method(self, server, tunnel_client):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance

        WHEN: An invalid method is called

        THEN: The server should raise an NotFoundError
        """
        with pytest.raises(NotFoundError):
            await tunnel_client._call_server('invalid_method')

    @pytest.mark.asyncio
    @pytest.mark.requires_sudo
    @pytest.mark.real_device
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_start_tunnel(self, server, tunnel_client, device_udid):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance
        AND: A real UDID

        WHEN: `TunnelClient.start_tunnel` is called

        THEN: The function should return a tunnel result
        """
        tunnel_result = await tunnel_client.start_tunnel(device_udid)

        assert tunnel_result is not None
        assert tunnel_result.protocol == TunnelProtocol.TCP
        assert tunnel_result.address
        assert tunnel_result.port

    @pytest.mark.asyncio
    @pytest.mark.requires_sudo
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_start_tunnel_no_device(self, server, tunnel_client):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance

        WHEN: `TunnelClient.start_tunnel` is called with a non-existing UDID

        THEN: The function should raise a DeviceNotFoundError
        """
        with pytest.raises(DeviceNotFoundError):
            await tunnel_client.start_tunnel('invalid_udid')

    @pytest.mark.asyncio
    @pytest.mark.requires_sudo
    @pytest.mark.real_device
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_start_tunnel_already_started(self, server, tunnel_client, device_udid):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance
        AND: A real UDID

        WHEN: `TunnelClient.start_tunnel` is called twice with the same UDID

        THEN: The function should raise a TunnelAlreadyExistsError
        """

        await tunnel_client.start_tunnel(device_udid)

        with pytest.raises(TunnelAlreadyExistsError):
            await tunnel_client.start_tunnel(device_udid)

    @pytest.mark.asyncio
    @pytest.mark.requires_sudo
    @pytest.mark.real_device
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_stop_tunnel(self, server, tunnel_client, device_udid):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance
        AND: A real UDID
        AND: A started tunnel task

        WHEN: `TunnelClient.stop_tunnel` is called

        THEN: The get_tunnel method should return None
        """
        await tunnel_client.start_tunnel(device_udid)

        await tunnel_client.stop_tunnel(device_udid)

        assert await tunnel_client.get_tunnel(device_udid) is None

    @pytest.mark.asyncio
    @pytest.mark.requires_sudo
    @pytest.mark.real_device
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_get_tunnel(self, server, tunnel_client, device_udid):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance
        AND: A real UDID
        AND: A started tunnel task

        WHEN: `TunnelClient.get_tunnel` is called

        THEN: The tunnel result should match the started tunnel result
        """
        started_tunnel = await tunnel_client.start_tunnel(device_udid)

        tunnel_result = await tunnel_client.get_tunnel(device_udid)

        assert tunnel_result is not None
        assert tunnel_result == started_tunnel

    @pytest.mark.asyncio
    @pytest.mark.parametrize("server", ["tunnel_server", "tunnel_server_subprocess"], indirect=True)
    async def test_get_non_existing_tunnel(self, server, tunnel_client):
        """
        GIVEN: A TunnelServer running
        AND: A TunnelClient instance

        WHEN: `TunnelClient.get_tunnel` is called with a non-existing UDID

        THEN: The called method should return None.
        """
        assert await tunnel_client.get_tunnel('invalid_udid') is None

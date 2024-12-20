import asyncio
import time

import pytest

from core.async_socket import ServerSocket, ClientSocket
from core.codec.socket_json_codec import ClientRequest, ServerResponse
from tests.test_data.socket_test_data import VALID_REQUESTS, VALID_RESPONSES, TIMEOUTS


class TestSocket:
    @pytest.mark.asyncio
    async def test_client_not_waiting_after_send(self, port):
        """
        GIVEN: A client socket
        AND: A server socket
        AND: A request

        WHEN: The client sends a message
        AND: The client does not wait for a response (closes the connection)
        AND: The server tries to receive a message

        THEN: The server should raise a TimeoutError
        """

        async def client_send_message(message: ClientRequest):
            with ClientSocket(port=port) as client_socket:
                await client_socket.send(message)

        async def server_receive_message():
            with ServerSocket(port=port) as server_socket:
                with pytest.raises(TimeoutError):
                    await server_socket.receive()

        for valid_request in VALID_REQUESTS:
            await asyncio.gather(
                server_receive_message(),
                client_send_message(valid_request),
            )

    @pytest.mark.asyncio
    async def test_server_not_responding(self, port):
        """
        GIVEN: A client socket
        AND: A server socket
        AND: A request

        WHEN: The client sends the request
        AND: The server receives
        AND: The server does not respond
        AND: The client tries to receive any response

        THEN: The client should raise a TimeoutError
        """

        async def client_send_message(message: ClientRequest):
            with ClientSocket(port=port) as client_socket:
                await client_socket.send(message)
                with pytest.raises(TimeoutError):
                    await client_socket.receive()

        async def server_receive_message():
            with ServerSocket(port=port) as server_socket:
                await server_socket.receive()

        for valid_request in VALID_REQUESTS:
            await asyncio.gather(
                server_receive_message(),
                client_send_message(valid_request),
            )

    @pytest.mark.asyncio
    async def test_server_receives_the_correct_request(self, port):
        """
        GIVEN: A client socket
        AND: A server socket
        AND: A request

        WHEN: The client sends the request
        AND: The server receives the request

        THEN: The server should receive the exact same request as the one sent by the client
        """

        async def client_send_message(message: ClientRequest):
            with ClientSocket(port=port) as client_socket:
                await client_socket.send(message)
                # We need to wait for a bit to make sure the message is actually sent
                await asyncio.sleep(0.001)

        async def server_receive_message(message: ClientRequest):
            with ServerSocket(port=port) as server_socket:
                received_request = await server_socket.receive()

                assert received_request is not None
                assert received_request.model_dump() == message.model_dump()

        for valid_request in VALID_REQUESTS:
            await asyncio.gather(
                server_receive_message(valid_request),
                client_send_message(valid_request),
            )

    @pytest.mark.asyncio
    async def test_server_client_full_communication(self, port):
        """
        GIVEN: A client socket
        AND: A server socket
        AND: A request
        AND: A response

        WHEN: The client sends the request
        AND: The server receives
        AND: The server responds with the response

        THEN: The client should receive the exact same response as the one sent by the server
        """

        async def client_receive_message(
            request: ClientRequest, response: ServerResponse
        ):
            with ClientSocket(port=port) as client_socket:
                await client_socket.send(request)
                # We need to wait to make sure the message is sent and received by the server
                await asyncio.sleep(0)
                received_response = await client_socket.receive()
                assert received_response.model_dump() == response.model_dump()

        async def server_send_message(response: ServerResponse):
            with ServerSocket(port=port) as server_socket:
                await server_socket.receive()
                await server_socket.respond(response)

        for valid_response in VALID_RESPONSES:
            for valid_request in VALID_REQUESTS:
                await asyncio.gather(
                    server_send_message(valid_response),
                    client_receive_message(valid_request, valid_response),
                )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("socket_type", ["client", "server"])
    @pytest.mark.parametrize("timeout", TIMEOUTS)
    async def test_server_receive_timeout(
        self, socket_type, client_socket, server_socket, timeout
    ):
        """
        GIVEN: A server or client socket
        AND: A timeout

        WHEN: Trying to receive a request with the given timeout
        AND: And nothing is sent

        THEN: A TimeoutError should be raised
        AND: The time passed should be equal or greater to the timeout
        """

        def _assert_time_passed(start: float, end: float):
            """Assert that the time passed between two points is equal or greater to the given timeout"""
            elapsed_time = end - start
            if timeout is None:
                assert elapsed_time >= 0.1
            else:
                assert elapsed_time >= timeout.total_seconds()

        start_time = time.perf_counter()
        with pytest.raises(TimeoutError):
            if socket_type == "server":
                await server_socket.receive(timeout=timeout)
            elif socket_type == "client":
                await client_socket.receive(timeout=timeout)
            else:
                pytest.fail(f"Invalid socket type: {socket_type}")
        end_time = time.perf_counter()
        _assert_time_passed(start_time, end_time)

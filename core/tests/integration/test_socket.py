import asyncio

import pytest

from core.socket import ServerSocket, ClientSocket, ClientRequest, ServerResponse
from tests.test_data.socket_test_data import VALID_REQUESTS, VALID_RESPONSES


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
            with ClientSocket(port) as client_socket:
                await client_socket.send(message)

        async def server_receive_message():
            with ServerSocket(port) as server_socket:
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
            with ClientSocket(port) as client_socket:
                await client_socket.send(message)
                with pytest.raises(TimeoutError):
                    await client_socket.receive()

        async def server_receive_message():
            with ServerSocket(port) as server_socket:
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
            with ClientSocket(port) as client_socket:
                await client_socket.send(message)
                # We need to wait for a bit to make sure the message is actually sent
                await asyncio.sleep(0.001)

        async def server_receive_message(message: ClientRequest):
            with ServerSocket(port) as server_socket:
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

        async def client_receive_message(request: ClientRequest, response: ServerResponse):
            with ClientSocket(port) as client_socket:
                await client_socket.send(request)
                # We need to wait to make sure the message is sent and received by the server
                await asyncio.sleep(0)
                received_response = await client_socket.receive()
                assert received_response.model_dump() == response.model_dump()

        async def server_send_message(response: ServerResponse):
            with ServerSocket(port) as server_socket:
                await server_socket.receive()
                await server_socket.respond(response)

        for valid_response in VALID_RESPONSES:
            for valid_request in VALID_REQUESTS:
                await asyncio.gather(
                    server_send_message(valid_response),
                    client_receive_message(valid_request, valid_response),
                )

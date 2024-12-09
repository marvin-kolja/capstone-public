import datetime
import time
from datetime import timedelta

import pytest
import zmq

from core.exceptions.socket import InvalidSocketMessage
from core.socket import BaseMessage, SocketMessageFactory, ErrorResponse, ClientRequest, SuccessResponse, \
    HeartbeatRequest, \
    SocketMessageCodec, ServerSocket, ClientSocket, ServerSocketMessageCodec, ClientSocketMessageCodec
from tests.test_data.socket_test_data import VALID_MESSAGES, VALID_REQUESTS, VALID_RESPONSES, INVALID_MESSAGE_DATA, \
    INVALID_TIMESTAMPS


class TestMessage:
    def test_timestamp_as_datetime(self):
        """
        GIVEN: A POSIX timestamp in milliseconds
        AND: A BaseMessage instance instantiated with the timestamp

        WHEN: Accessing the timestamp_as_datetime property

        THEN: A datetime object should be returned with the same timestamp as the one used to instantiate the message
        """
        now = datetime.datetime.now(datetime.UTC)
        now = now.replace(microsecond=0)  # Base message only supports milliseconds
        posix_timestamp_millis = int(now.timestamp() * 1e3)

        message = BaseMessage(
            message_type="request",
            timestamp=posix_timestamp_millis,
        )
        assert message.timestamp_as_datetime == now

    def test_invalid_timestamp(self):
        """
        GIVEN: A BaseMessage instance with an invalid POSIX timestamp

        WHEN: Instantiating the message

        THEN: A ValueError should be raised
        """
        for invalid_timestamp in INVALID_TIMESTAMPS:
            with pytest.raises(ValueError):
                BaseMessage(
                    message_type="request",
                    timestamp=invalid_timestamp,
                )


class TestSocketMessageCodec:
    def test_encode_decode(self):
        """
        GIVEN: A list of valid messages

        WHEN: Encoding
        AND: Then decoding the messages again

        THEN: The decoded messages should be equal to the original messages
        """
        for message in VALID_MESSAGES:
            encoded_message = SocketMessageCodec.encode_message(message)
            decoded_message = SocketMessageCodec.decode_message(encoded_message)
            assert decoded_message.model_dump() == message.model_dump()

    INVALID_ENCODED_MESSAGES = [
        # Valid JSON but not invalid message
        b'{"message_type": "invalid"}',
        b'{"message_type": "request"}',
        b'{"message_type": "response"}',
        b'["message_type": "response"]',
        b'I am a string',
        b'0',
        # Not UTF-8 encoded bytes
        bytes(1),
        (1234).to_bytes(2, 'big'),
        bytes([0x01, 0x02, 0x03, 0x04]),
        # Invalid JSON
        b'{"message_type": "response"',
    ]

    def test_invalid_encoded_message(self):
        """
        GIVEN: A list of invalid encoded messages

        WHEN: Decoding the messages

        THEN: An InvalidSocketMessage exception should be raised
        """
        for encoded_message in self.INVALID_ENCODED_MESSAGES:
            with pytest.raises(InvalidSocketMessage):
                SocketMessageCodec.decode_message(encoded_message)


# The behavior map is used to determine the message type to use for each encoding/decoding test
behavior_map = {
    ("server", "decode"): {
        "decode_success_type": "request",
        "decode_fail_type": "response",
    },
    ("server", "encode"): {
        "encode_success_type": "response",
        "encode_fail_type": "request",
    },
    ("client", "decode"): {
        "decode_success_type": "response",
        "decode_fail_type": "request",
    },
    ("client", "encode"): {
        "encode_success_type": "request",
        "encode_fail_type": "response",
    },
}


@pytest.mark.parametrize("codec_class,role", [
    (ServerSocketMessageCodec, "server"),
    (ClientSocketMessageCodec, "client")
])
class TestDecoding:
    def test_decode_success_type(self, codec_class, role, spy_socket_decode):
        """
        GIVEN: A codec class
        AND: A list of valid messages for the codec

        WHEN: Decoding the encoded versions of the messages

        THEN: The decoded messages should be equal to the original messages
        AND: The decode_message method of the parent codec class should be called for each message
        """
        success_type = behavior_map[(role, "decode")]["decode_success_type"]
        messages = VALID_REQUESTS if success_type == "request" else VALID_RESPONSES

        for message in messages:
            encoded_message = SocketMessageCodec.encode_message(message)
            decoded_message = codec_class.decode_message(encoded_message)
            assert decoded_message.model_dump() == message.model_dump()

        assert spy_socket_decode.call_count == len(messages)

    def test_decode_fail_type(self, codec_class, role, spy_socket_decode):
        """
        GIVEN: A codec class
        AND: A list of invalid messages for the codec

        WHEN: Decoding the encoded versions of the messages

        THEN: An InvalidSocketMessage exception should be raised for each
        AND: The decode_message method of the parent codec class should be called for each message
        """
        fail_type = behavior_map[(role, "decode")]["decode_fail_type"]
        messages = VALID_REQUESTS if fail_type == "request" else VALID_RESPONSES

        for message in messages:
            encoded_message = SocketMessageCodec.encode_message(message)
            with pytest.raises(InvalidSocketMessage):
                codec_class.decode_message(encoded_message)

        assert spy_socket_decode.call_count == len(messages)


@pytest.mark.parametrize("codec_class,role", [
    (ServerSocketMessageCodec, "server"),
    (ClientSocketMessageCodec, "client")
])
class TestEncoding:
    def test_encode_success_type(self, codec_class, role, spy_socket_encode):
        """
        GIVEN: A codec class
        AND: A list of valid messages for the codec

        WHEN: Encoding the messages

        THEN: The encoded messages should be equal to the original messages encoded as bytes
        AND: The encode_message method of the parent codec class should be called for each message
        """
        success_type = behavior_map[(role, "encode")]["encode_success_type"]
        messages = VALID_REQUESTS if success_type == "request" else VALID_RESPONSES

        for message in messages:
            encoded_message = codec_class.encode_message(message)
            assert encoded_message == message.encode()

        assert spy_socket_encode.call_count == len(messages)

    def test_encode_fail_type(self, codec_class, role, spy_socket_encode):
        """
        GIVEN: A codec class
        AND: A list of invalid messages for the codec

        WHEN: Encoding the messages

        THEN: An InvalidSocketMessage exception should be raised for each
        AND: The encode_message method of the parent codec class should not be called
        """
        fail_type = behavior_map[(role, "encode")]["encode_fail_type"]
        messages = VALID_REQUESTS if fail_type == "request" else VALID_RESPONSES

        for message in messages:
            with pytest.raises(InvalidSocketMessage):
                codec_class.encode_message(message)

        # If the message is invalid, the encode_message method should not be called
        assert spy_socket_encode.call_count == 0


class TestSocketMessageFactory:
    def test_parse_message_data(self):
        """
        GIVEN: A list of valid messages

        WHEN: Parsing the model dump of the messages

        THEN: The parsed messages should be equal to the original messages
        """
        for message in VALID_MESSAGES:
            message_data = message.model_dump()
            parsed_message = SocketMessageFactory.parse_message_data(message_data)
            assert parsed_message.model_dump() == message.model_dump()

    def test_invalid_message_data(self):
        """
        GIVEN: A list of invalid message data

        WHEN: Parsing the message data

        THEN: An InvalidSocketMessage exception should be raised for each
        """
        for message_data in INVALID_MESSAGE_DATA:
            with pytest.raises(InvalidSocketMessage):
                SocketMessageFactory.parse_message_data(message_data)

    def test_invalid_timestamps(self):
        """
        GIVEN: A list of invalid timestamps

        WHEN: Parsing message data with the invalid timestamps

        THEN: An InvalidSocketMessage exception should be raised for each
        """
        for invalid_timestamp in INVALID_TIMESTAMPS:
            with pytest.raises(InvalidSocketMessage):
                SocketMessageFactory.parse_message_data({
                    "message_type": "request",
                    "action": "heartbeat",
                    "timestamp": invalid_timestamp,
                })

    def test_missing_fields(self):
        """
        GIVEN: A list of message data with missing fields

        WHEN: Parsing the message data

        THEN: An InvalidSocketMessage exception should be raised for each
        """
        with pytest.raises(InvalidSocketMessage):
            SocketMessageFactory.parse_message_data({
                "message_type": "request",
                "timestamp": "2021-01-01T00:00:00",
            })


timeouts = [
    timedelta(seconds=1),
    timedelta(seconds=0.5),
    timedelta(seconds=0.1),
    None,
]


def _assert_time_passed(start_time: float, end_time: float, timeout: timedelta = None):
    """ Assert that the time passed between two points is equal or greater to the given timeout """
    elapsed_time = end_time - start_time
    if timeout is None:
        assert elapsed_time >= 0.1
    else:
        assert elapsed_time >= timeout.total_seconds()


class TestClientSocket:
    success_response = SuccessResponse(
        message="Success",
        data={},
    )

    error_response = ErrorResponse(
        message="Error",
        error_code=0,
    )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("use_context_manager", [True, False])
    async def test_connect(self, port, use_context_manager):
        """
        GIVEN: A port number
        AND: A boolean indicating whether to use a context manager

        WHEN: Calling the connect method of the ClientSocket class

        THEN: The socket should not be closed
        AND: The last endpoint port should be equal to the given port
        """

        def assertions(client):
            assert client._socket is not None
            assert client._socket.closed is False
            last_endpoint = client._socket.getsockopt_string(zmq.LAST_ENDPOINT)
            last_endpoint_port = last_endpoint.split(":")[-1]
            assert last_endpoint_port == str(port)

        if use_context_manager:
            with ClientSocket(port=port) as c:
                assertions(c)
        else:
            c = ClientSocket(port=port)
            c.connect()
            assertions(c)
            c.close()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[success_response.encode()]], indirect=True)
    @pytest.mark.parametrize("client_request", VALID_REQUESTS)
    async def test_send(self, mock_zmq_context, client_socket, client_request):
        """
        GIVEN: A client socket with a mocked send method
        AND: A client request

        WHEN: Sending the client request

        THEN: The mocked ZMQ socket `send_multipart` method should be called with the encoded client request
        """
        await client_socket.send(client_request)

        mock_zmq_context.send_multipart.assert_called_once_with(
            [client_socket._codec.encode_message(client_request)]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[success_response.encode()]], indirect=True)
    async def test_receive(self, mock_zmq_context, mock_zmq_poller, client_socket):
        """
        GIVEN: A client socket with a mocked receive response and poller

        WHEN: Receiving a response

        THEN: The response should be equal to the success response
        AND: The pollers poll method should be called with a timeout of 100 milliseconds
        """
        response = await client_socket.receive()
        assert isinstance(response, SuccessResponse)
        assert response == self.success_response

        mock_zmq_poller.poll.assert_called_once_with(100)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeout", timeouts)
    async def test_receive_timout(self, timeout):
        """
        GIVEN: A client socket
        AND: A timeout

        WHEN: Trying to receive a response with the given timeout
        AND: No response is sent

        THEN: A TimeoutError should be raised
        AND: The time passed should be equal or greater to the timeout
        """
        with ClientSocket(12345) as client:
            start_time = time.perf_counter()
            with pytest.raises(TimeoutError):
                await client.receive(timeout=timeout)
            end_time = time.perf_counter()
            _assert_time_passed(start_time, end_time, timeout)

    def test_close(self, spy_zmq_socket_close, spy_zmq_context_term, client_socket):
        """
        GIVEN: A client socket has been connected and used for communication

        WHEN: Closing the client socket

        THEN: The ZMQ socket close method should be called
        AND: The ZMQ context term method should be called
        """
        socket = client_socket._socket

        client_socket.close()

        assert client_socket._socket is None
        spy_zmq_socket_close.assert_called_once()
        spy_zmq_context_term.assert_called_once()
        assert socket.closed is True


class TestServerSocket:
    ports = [12345, None]
    heartbeat_request = HeartbeatRequest()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("port", ports)
    @pytest.mark.parametrize("use_context_manager", [True, False])
    async def test_start_server(self, port, use_context_manager):
        """
        GIVEN: A port number
        AND: A boolean indicating whether to use a context manager

        WHEN: Starting a server socket

        THEN: The server should be started
        AND: The port should be equal to the given port
        """

        def assertions():
            assert server._socket is not None
            assert server._socket.closed is False
            socket_port = server._socket.getsockopt(zmq.LAST_ENDPOINT).decode().split(":")[-1]
            if port is None:
                assert socket_port == str(server.port)
            else:
                assert server.port == port
                assert socket_port == str(port)

        if use_context_manager:
            with ServerSocket(port=port) as server:
                assertions()
        else:
            server = ServerSocket(port=port)
            server.start()
            assertions()
            server.close()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeout", timeouts)
    async def test_receive_timeout(self, server_socket, timeout):
        """
        GIVEN: A server socket
        AND: A timeout

        WHEN: Trying to receive a request with the given timeout
        AND: No request is sent

        THEN: A TimeoutError should be raised
        AND: The time passed should be equal or greater to the timeout
        """
        start_time = time.perf_counter()
        with pytest.raises(TimeoutError):
            await server_socket.receive(timeout=timeout)
        end_time = time.perf_counter()
        _assert_time_passed(start_time, end_time, timeout)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[heartbeat_request.encode()]], indirect=True)
    async def test_receive(self, mock_zmq_context, server_socket):
        """
        GIVEN: A server socket with a mocked receive method

        WHEN: Receiving an encoded heartbeat request

        THEN: The mocked ZMQ socket `recv_multipart` method should be called
        AND: the request should be equal to the heartbeat request
        """
        request = await server_socket.receive()
        assert isinstance(request, HeartbeatRequest)
        assert request == self.heartbeat_request

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[heartbeat_request.encode()]], indirect=True)
    async def test_respond(self, mock_zmq_context, server_socket):
        """
        GIVEN: A server socket with a mocked send method

        WHEN: Responding

        THEN: The mocked zmq socket `send_multipart` method should be called with the encoded response
        """
        success_response = SuccessResponse(message="Success", data={})

        await server_socket.respond(success_response)

        mock_zmq_context.send_multipart.assert_called_once_with(
            [success_response.encode()]
        )

    @pytest.mark.asyncio
    async def test_respond_before_receiving(self, server_socket):
        """
        GIVEN: A server socket

        WHEN: The server tries to respond before having received a message

        THEN: The server should raise a ZMQError
        """
        with pytest.raises(zmq.error.ZMQError):
            await server_socket.respond(SuccessResponse())

    def test_close(self, spy_zmq_socket_close, spy_zmq_context_term, server_socket):
        """
        GIVEN: A server socket has been started

        WHEN: Closing the server socket

        THEN: The ZMQ socket close method should be called
        AND: The ZMQ context term method should be called
        """
        socket = server_socket._socket

        server_socket.close()

        assert server_socket._socket is None
        spy_zmq_socket_close.assert_called_once()
        spy_zmq_context_term.assert_called_once()
        assert socket.closed is True

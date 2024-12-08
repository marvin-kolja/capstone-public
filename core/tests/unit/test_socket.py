import sys
from datetime import timedelta

import pytest

from core.exceptions.socket import InvalidSocketMessage
from core.socket import BaseMessage, SocketMessageFactory, ErrorResponse, ClientRequest, SuccessResponse, \
    HeartbeatRequest, \
    SocketMessageCodec, ServerSocket, ClientSocket, ServerSocketMessageCodec, ClientSocketMessageCodec

invalid_timestamps = [
    # Invalid timestamp
    "2021-01-01T00:00:00",
    # Invalid Unix timestamp
    123.456,
    # Out of range Unix timestamp
    sys.maxsize
]


class TestMessage:
    def test_timestamp_as_datetime(self):
        message = BaseMessage(
            message_type="request",
            timestamp=1612137600000,
        )
        assert message.timestamp_as_datetime.isoformat() == "2021-02-01T00:00:00+00:00"

    @pytest.mark.parametrize("timestamp", invalid_timestamps)
    def test_invalid_timestamp(self, timestamp):
        with pytest.raises(ValueError):
            BaseMessage(
                message_type="request",
                timestamp=timestamp,
            )


valid_requests = [
    ClientRequest(
        action="some_action",
        data={
            "some_string": "Hello, World!",
            "some_int": 42,
            "some_float": 3.14,
        }

    ),
    ClientRequest(
        action="some_action",
        data={
            "some_string": "Hello, World!",
            "some_int": 42,
            "some_float": 3.14,
        },
        timestamp=1612137600000,
    ),
    HeartbeatRequest()
]

valid_responses = [
    ErrorResponse(
        message="Internal Error",
        error_code=0,
    ),
    ErrorResponse(
        message="Internal Error",
        error_code=0,
        timestamp=1612137600000,
    ),
    SuccessResponse(
        message="Hello, World!",
        data={
            "some_string": "Hello, World!",
            "some_int": 42,
            "some_float": 3.14,
        }

    ),
    SuccessResponse(
        message="Hello, World!",
        data={
            "some_string": "Hello, World!",
            "some_int": 42,
            "some_float": 3.14,
        },
        timestamp=1612137600000,
    ),
]

valid_messages = valid_requests + valid_responses

valid_timestamp = 1612137600000

invalid_request_data = [
    # No action field
    {
        "message_type": "request",
        "timestamp": valid_timestamp,
    },
    # Incorrect data type
    {
        "message_type": "request",
        "timestamp": valid_timestamp,
        "data": [],
    },
    {
        "message_type": "request",
        "timestamp": valid_timestamp,
        "data": 1,
    },
    {
        "message_type": "request",
        "timestamp": valid_timestamp,
        "data": "Hello, World!",
    },
]

invalid_response_data = [
    # No error_code field
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
        "status": "ERROR",
    },
    # Invalid status field
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
        "status": "INVALID",
    },
    # Incorrect data type
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
        "status": "ERROR",
    },
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
        "status": "ERROR",
        "error_code": 0.1,
    },
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
        "status": "OK",
        "data": 1,
    },
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
        "status": "OK",
        "data": "Hello, World!",
    },
    # No status field
    {
        "message_type": "response",
        "timestamp": valid_timestamp,
    },
]

invalid_messages_data = [
    # No data
    {},
    # Invalid message type
    {
        "message_type": "invalid",
        "timestamp": valid_timestamp,
    },
    {
        "timestamp": valid_timestamp,
    },
]
invalid_messages_data += invalid_request_data + invalid_response_data
invalid_messages_data += [
    message.model_dump(exclude={"timestamp"}) for message in valid_messages
]


class TestSocketMessageCodec:
    @pytest.mark.parametrize("message", valid_messages)
    def test_encode_decode(self, message):
        encoded_message = SocketMessageCodec.encode_message(message)
        decoded_message = SocketMessageCodec.decode_message(encoded_message)
        assert decoded_message.model_dump() == message.model_dump()

    invalid_encoded_messages = [
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

    @pytest.mark.parametrize("encoded_message", invalid_encoded_messages)
    def test_invalid_encoded_message(self, encoded_message):
        with pytest.raises(InvalidSocketMessage):
            SocketMessageCodec.decode_message(encoded_message)


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
        success_type = behavior_map[(role, "decode")]["decode_success_type"]
        messages = valid_requests if success_type == "request" else valid_responses

        for message in messages:
            encoded_message = SocketMessageCodec.encode_message(message)
            decoded_message = codec_class.decode_message(encoded_message)
            assert decoded_message.model_dump() == message.model_dump()

        assert spy_socket_decode.call_count == len(messages)

    def test_decode_fail_type(self, codec_class, role, spy_socket_decode):
        fail_type = behavior_map[(role, "decode")]["decode_fail_type"]
        messages = valid_requests if fail_type == "request" else valid_responses

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
        success_type = behavior_map[(role, "encode")]["encode_success_type"]
        messages = valid_requests if success_type == "request" else valid_responses

        for message in messages:
            encoded_message = codec_class.encode_message(message)
            assert encoded_message == message.encode()

        assert spy_socket_encode.call_count == len(messages)

    def test_encode_fail_type(self, codec_class, role, spy_socket_encode):
        fail_type = behavior_map[(role, "encode")]["encode_fail_type"]
        messages = valid_requests if fail_type == "request" else valid_responses

        for message in messages:
            with pytest.raises(InvalidSocketMessage):
                codec_class.encode_message(message)

        assert spy_socket_encode.call_count == len(messages)


class TestSocketMessageFactory:
    @pytest.mark.parametrize("message", valid_messages)
    def test_parse_message_data(self, message):
        message_data = message.model_dump()
        parsed_message = SocketMessageFactory.parse_message_data(message_data)
        assert parsed_message.model_dump() == message.model_dump()

    @pytest.mark.parametrize("message_data", invalid_messages_data)
    def test_invalid_message_data(self, message_data):
        with pytest.raises(InvalidSocketMessage):
            SocketMessageFactory.parse_message_data(message_data)

    @pytest.mark.parametrize("timestamp", invalid_timestamps)
    def test_invalid_timestamps(self, timestamp):
        with pytest.raises(InvalidSocketMessage):
            SocketMessageFactory.parse_message_data({
                "message_type": "request",
                "action": "heartbeat",
                "timestamp": timestamp,
            })

    def test_missing_fields(self):
        with pytest.raises(InvalidSocketMessage):
            SocketMessageFactory.parse_message_data({
                "message_type": "request",
                "timestamp": "2021-01-01T00:00:00",
            })


timeouts = [
    timedelta(seconds=0.1),
    None,
]

ports = [12345, None]


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
    @pytest.mark.parametrize("port", ports)
    async def test_connect(self, port):
        with ClientSocket(port=port) as client:
            assert client._socket is not None
            assert client._socket.closed is False
            if port is None:
                assert client.port > 0
                assert client._socket.getpeername()[1] == client.port
            else:
                assert client.port == port
                assert client._socket.getpeername()[1] == port

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[success_response.encode()]], indirect=True)
    @pytest.mark.parametrize("client_request", valid_requests)
    async def test_send(self, mock_zmq_context, client_socket, client_request):
        await client_socket.send(client_request)

        mock_zmq_context.send_multipart.assert_called_once_with(
            [client_socket._codec.encode_message(client_request)]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[success_response.encode()]], indirect=True)
    async def test_receive(self, mock_zmq_context, mock_zmq_poller, client_socket):
        response = await client_socket.receive()
        assert isinstance(response, SuccessResponse)
        assert response == self.success_response

        mock_zmq_poller.poll.assert_called_once_with(100)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeout", timeouts)
    async def test_receive_timout(self, timeout):
        with ClientSocket(12345) as client:
            with pytest.raises(TimeoutError):
                await client.receive(timeout=timeout)

    @pytest.mark.parametrize("mock_zmq_context", [[success_response.encode()]], indirect=True)
    def test_close(self, mock_zmq_context, client_socket):
        socket = client_socket._socket

        client_socket.close()

        assert client_socket._socket is None
        assert mock_zmq_context.term.called is True
        assert socket.closed is True


class TestServerSocket:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("port", ports)
    async def test_start_server_with_port(self, port):
        with ServerSocket(port=port) as server:
            if port is None:
                assert server.port > 0
                assert server._socket.getsockname()[1] == server.port
            else:
                assert server.port == port
                assert server._socket.getsockname()[1] == port

    @pytest.mark.asyncio
    @pytest.mark.parametrize("port", ports)
    async def test_not_using_context_manager(self, port):
        server = ServerSocket(port=port)
        server.start()
        if port is None:
            assert server.port > 0
            assert server._socket.getsockname()[1] == server.port
        else:
            assert server.port == port
            assert server._socket.getsockname()[1] == port
        server.close()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeout", timeouts)
    async def test_receive_timeout(self, server_socket, timeout):
        with pytest.raises(TimeoutError):
            await server_socket.receive(timeout=timeout)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[HeartbeatRequest().encode()]], indirect=True)
    async def test_receive(self, mock_zmq_context, server_socket):
        request = await server_socket.receive()
        assert isinstance(request, HeartbeatRequest)
        assert request == HeartbeatRequest()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[HeartbeatRequest().encode()]], indirect=True)
    async def test_respond(self, mock_zmq_context, server_socket):
        await server_socket.respond(SuccessResponse(message="Success", data={}))

        mock_zmq_context.send_multipart.assert_called_once_with(
            [SuccessResponse(message="Success", data={}).encode()]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_zmq_context", [[HeartbeatRequest().encode()]], indirect=True)
    async def test_close(self, mock_zmq_context, server_socket):
        socket = server_socket._socket

        server_socket.close()

        assert server_socket._socket is None
        assert mock_zmq_context.term.called is True
        assert socket.closed is True

import sys

import pytest

from core.exceptions.socket import InvalidSocketMessage
from core.socket import BaseMessage, SocketMessageFactory, ErrorResponse, ClientRequest, SuccessResponse, \
    HeartbeatRequest, \
    SocketMessageCodec

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

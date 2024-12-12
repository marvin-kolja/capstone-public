import sys
from datetime import timedelta

from core.codec.socket_json_codec import ClientRequest, HeartbeatRequest, ErrorResponse, SuccessResponse

INVALID_TIMESTAMPS = [
    # Invalid timestamp
    "2021-01-01T00:00:00",
    # Invalid Unix timestamp
    123.456,
    # Out of range Unix timestamp
    sys.maxsize
]

VALID_REQUESTS = [
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

VALID_RESPONSES = [
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

VALID_MESSAGES = VALID_REQUESTS + VALID_RESPONSES

VALID_TIMESTAMP = 1612137600000

INVALID_REQUEST_DATA = [
    # No action field
    {
        "message_type": "request",
        "timestamp": VALID_TIMESTAMP,
    },
    # Incorrect data type
    {
        "message_type": "request",
        "timestamp": VALID_TIMESTAMP,
        "data": [],
    },
    {
        "message_type": "request",
        "timestamp": VALID_TIMESTAMP,
        "data": 1,
    },
    {
        "message_type": "request",
        "timestamp": VALID_TIMESTAMP,
        "data": "Hello, World!",
    },
]

INVALID_RESPONSE_DATA = [
    # No error_code field
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
        "status": "ERROR",
    },
    # Invalid status field
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
        "status": "INVALID",
    },
    # Incorrect data type
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
        "status": "ERROR",
    },
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
        "status": "ERROR",
        "error_code": 0.1,
    },
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
        "status": "OK",
        "data": 1,
    },
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
        "status": "OK",
        "data": "Hello, World!",
    },
    # No status field
    {
        "message_type": "response",
        "timestamp": VALID_TIMESTAMP,
    },
]

INVALID_MESSAGE_DATA = [
    # No data
    {},
    # Invalid message type
    {
        "message_type": "invalid",
        "timestamp": VALID_TIMESTAMP,
    },
    {
        "timestamp": VALID_TIMESTAMP,
    },
]
INVALID_MESSAGE_DATA += INVALID_REQUEST_DATA + INVALID_RESPONSE_DATA
INVALID_MESSAGE_DATA += [
    message.model_dump(exclude={"timestamp"}) for message in VALID_MESSAGES
]

TIMEOUTS = [
    timedelta(seconds=1),
    timedelta(seconds=0.1),
    timedelta(milliseconds=100),
    timedelta(microseconds=1000),
    timedelta(microseconds=1),
    timedelta(0),
    None,
]

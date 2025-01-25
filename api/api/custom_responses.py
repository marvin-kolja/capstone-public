from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse, JSONResponse


class SSEStreamingResponse(StreamingResponse):
    media_type = "text/event-stream"


class HTTPExceptionResponse(JSONResponse):
    """
    Custom JSON response for HTTP exceptions.
    """

    def __init__(self, status_code: int, detail: Any, headers: dict = None):
        super().__init__(
            status_code=status_code,
            content=jsonable_encoder(
                HTTPExceptionContent(code=status_code, detail=detail),
            ),
            headers=headers,
            media_type="application/json",
        )


class HTTPExceptionContent(BaseModel):
    """
    Common response body for HTTP exception JSON responses.
    """

    code: int = Field(..., title="Status Code")
    detail: str | None = Field(None, title="Exception Detail")


class ValidationError(BaseModel):
    """
    Validation error detail for HTTP 422 responses.

    Mirrors the FastAPI ValidationError model, but is required as error handling is done in a custom way.
    """

    loc: list[str | int] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class HTTPValidationError(HTTPExceptionContent):
    """
    Validation error response body for HTTP 422 responses.

    Mirrors the FastAPI HTTPValidationError model, but is required as error handling is done in a custom way.
    """

    detail: list[ValidationError]


def build_common_http_exception_responses(status_codes: list[int]) -> dict[int, dict]:
    """
    Build common HTTP exception responses for a list of status codes to be used in FastAPI route definitions.

    :param status_codes: List of status codes to build responses for.
    :return: Dictionary with status codes as keys and HTTPExceptionBody as values.
    """
    responses = {
        status_code: {
            "model": HTTPExceptionContent,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/HTTPExceptionContent"},
                }
            },
        }
        for status_code in status_codes
    }
    if 422 in status_codes:
        responses[422]["model"] = HTTPValidationError
        responses[422]["content"]["application/json"]["schema"] = {
            "$ref": "#/components/schemas/HTTPValidationError",
        }
    return responses

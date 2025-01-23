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
    detail: list | dict | str | None = Field(None, title="Exception Detail")

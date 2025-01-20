from starlette.responses import StreamingResponse


class SSEStreamingResponse(StreamingResponse):
    media_type = "text/event-stream"

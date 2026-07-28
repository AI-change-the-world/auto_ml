"""SSE 响应封装。"""
from sse_starlette.sse import EventSourceResponse, ServerSentEvent


def create_sse_response(generator, ping: int = 15) -> EventSourceResponse:
    return EventSourceResponse(
        generator,
        ping=ping,
        ping_message_factory=lambda: ServerSentEvent(comment="ping"),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

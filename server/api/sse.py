"""Server-Sent Events (SSE) utilities for streaming responses"""

import asyncio
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SSEEvent:
    """Server-Sent Event for streaming responses"""

    def __init__(self, event_type: str, data: Any):
        self.event_type = event_type
        self.data = data

    def to_sse_format(self) -> str:
        """Convert to SSE format string"""
        if isinstance(self.data, str):
            data_str = self.data
        else:
            data_str = json.dumps(self.data, ensure_ascii=False)

        # Escape newlines in data
        data_str = data_str.replace("\n", "\\n")

        return f"event: {self.event_type}\ndata: {data_str}\n\n"


async def sse_heartbeat_generator(conversation_id: str):
    """Generate SSE heartbeat events to keep connection alive"""
    heartbeat_count = 0
    while True:
        try:
            await asyncio.sleep(5)
            heartbeat_count += 1
            # Send heartbeat comment (SSE comments start with :)
            yield f": heartbeat {heartbeat_count}\n\n"
        except asyncio.CancelledError:
            logger.debug(f"SSE heartbeat cancelled for conversation {conversation_id}")
            break


def create_sse_response_headers() -> dict:
    """Create standard SSE response headers"""
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


def format_sse_error(error_message: str, conversation_id: Optional[str] = None) -> str:
    """Format an error as SSE event"""
    data = {"error": error_message}
    if conversation_id:
        data["conversation_id"] = conversation_id
    return SSEEvent("error", data).to_sse_format()


def format_sse_complete(
    conversation_id: str, message: str = "Conversation completed"
) -> str:
    """Format a completion event as SSE"""
    return SSEEvent(
        "complete", {"conversation_id": conversation_id, "message": message}
    ).to_sse_format()

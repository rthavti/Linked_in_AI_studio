import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.realtime import register_subscriber
from app.realtime import unregister_subscriber


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


def _format_sse(event_type: str, data: dict) -> str:
    payload = json.dumps(data, separators=(",", ":"))
    return f"event: {event_type}\ndata: {payload}\n\n"


@router.get("/stream")
async def stream_events(request: Request):
    queue = await register_subscriber()

    async def event_generator():
        try:
            yield _format_sse("connected", {"ok": True})

            while True:
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    yield _format_sse(event.get("type", "sync"), event)
                except TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            unregister_subscriber(queue)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)

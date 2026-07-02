import asyncio
from datetime import datetime, timezone
from typing import Any


_subscribers: set[asyncio.Queue] = set()
_event_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _event_loop
    _event_loop = loop


async def register_subscriber() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.add(queue)
    return queue


def unregister_subscriber(queue: asyncio.Queue) -> None:
    _subscribers.discard(queue)


def _broadcast(event: dict[str, Any]) -> None:
    stale: list[asyncio.Queue] = []
    for queue in _subscribers:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop oldest item to keep real-time updates flowing.
            try:
                queue.get_nowait()
                queue.put_nowait(event)
            except Exception:
                stale.append(queue)
        except Exception:
            stale.append(queue)

    for queue in stale:
        _subscribers.discard(queue)


def publish_event(event_type: str, payload: dict[str, Any] | None = None) -> None:
    loop = _event_loop
    if loop is None or not loop.is_running():
        return

    event = {
        "type": event_type,
        "payload": payload or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    loop.call_soon_threadsafe(_broadcast, event)

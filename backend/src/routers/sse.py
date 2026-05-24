"""SSE (Server-Sent Events) endpoint for task update broadcasting."""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.services.sse_manager import sse_manager
from src.utils.logger import logger

router = APIRouter(tags=["sse"])


async def sse_event_generator(request: Request):
    """Async generator that yields SSE-formatted events.

    Note: request.is_disconnected() is deliberately NOT used here because
    under a Vite/dev proxy the underlying transport can report disconnected
    prematurely, causing an endless connect/disconnect/reconnect cycle.
    Instead we rely on the yield raising an error or the task being
    cancelled when the client actually disconnects.
    """
    queue = await sse_manager.connect()

    try:
        while True:
            if sse_manager.shutdown_event.is_set():
                break

            try:
                # Short timeout so shutdown flag is polled frequently
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
                if message is None:
                    # Sentinel pushed by shutdown() — stop
                    break
                yield f"data: {message}\n\n"
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                # Use a comment line (SSE spec) so proxies don't buffer it
                yield ": heartbeat\n\n"
            except asyncio.CancelledError:
                break
    except asyncio.CancelledError:
        pass
    except Exception:
        # Client likely disconnected — yield/stream raised
        pass
    finally:
        await sse_manager.disconnect(queue)


@router.get("/events")
async def sse_events(request: Request):
    """SSE endpoint that streams task status change events to all connected clients."""
    return StreamingResponse(
        sse_event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

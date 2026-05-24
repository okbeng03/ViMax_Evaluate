"""SSE (Server-Sent Events) connection manager for broadcasting task updates."""

import asyncio
import json
from typing import Set
from datetime import datetime, timezone

from src.utils.logger import logger


class SSEManager:
    """Manages SSE connections for broadcasting task status changes."""

    def __init__(self):
        self._queues: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

    @property
    def shutdown_event(self) -> asyncio.Event:
        return self._shutdown_event

    async def shutdown(self) -> None:
        """Signal all SSE generators to stop (called during graceful shutdown)."""
        self._shutdown_event.set()
        # Push sentinel to every queue so any blocked queue.get() returns immediately
        async with self._lock:
            for queue in self._queues:
                try:
                    queue.put_nowait(None)
                except Exception:
                    pass

    async def connect(self) -> asyncio.Queue:
        """Register a new SSE client and return an event queue."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._queues.add(queue)
        logger.info(f"SSE client connected, total clients: {len(self._queues)}")
        return queue

    async def disconnect(self, queue: asyncio.Queue) -> None:
        """Remove an SSE client."""
        async with self._lock:
            self._queues.discard(queue)
        logger.info(f"SSE client disconnected, total clients: {len(self._queues)}")

    async def broadcast(self, event_type: str, data: dict) -> None:
        """Broadcast an event to all connected SSE clients."""
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        async with self._lock:
            queues = self._queues.copy()

        dead_queues: Set[asyncio.Queue] = set()
        for queue in queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(queue)
            except Exception:
                dead_queues.add(queue)

        if dead_queues:
            async with self._lock:
                for q in dead_queues:
                    self._queues.discard(q)

    async def broadcast_task_completed(self, task_id: str, overall_score: float) -> None:
        """Broadcast a task_completed event."""
        await self.broadcast("task_completed", {
            "task_id": task_id,
            "overall_score": overall_score,
        })

    async def broadcast_task_updated(self, task_id: str, status: str) -> None:
        """Broadcast a task_updated event."""
        await self.broadcast("task_updated", {
            "task_id": task_id,
            "status": status,
        })


sse_manager = SSEManager()

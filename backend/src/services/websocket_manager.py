"""WebSocket connection manager for real-time task updates."""

from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket
import asyncio
import json

from src.utils.logger import logger


class ConnectionManager:
    """Manages WebSocket connections for task updates."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """Accept and register a WebSocket connection for a task."""
        await websocket.accept()
        async with self._lock:
            if task_id not in self._connections:
                self._connections[task_id] = set()
            self._connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}", extra={"task_id": task_id})

    async def disconnect(self, websocket: WebSocket, task_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if task_id in self._connections:
                self._connections[task_id].discard(websocket)
                if not self._connections[task_id]:
                    del self._connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}", extra={"task_id": task_id})

    async def send_message(
        self,
        task_id: str,
        message_type: str,
        data: dict,
    ) -> None:
        """Send a message to all connections for a task."""
        message = {
            "type": message_type,
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        message_json = json.dumps(message)

        async with self._lock:
            connections = self._connections.get(task_id, set()).copy()

        if not connections:
            return

        disconnected = set()
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(websocket)

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if task_id in self._connections:
                        self._connections[task_id].discard(ws)

    async def send_status(
        self,
        task_id: str,
        status: str,
        progress: Optional[dict] = None,
    ) -> None:
        """Send status update to all connections for a task."""
        data = {"status": status}
        if progress:
            data["progress"] = progress
        await self.send_message(task_id, "status", data)

    async def send_result(
        self,
        task_id: str,
        clip_score: float,
        clip_interpretation: str,
        overall_score: float,
        llm_consistency: str,
    ) -> None:
        """Send evaluation result to all connections for a task."""
        data = {
            "clip_score": clip_score,
            "clip_interpretation": clip_interpretation,
            "overall_score": overall_score,
            "llm_consistency": llm_consistency,
        }
        await self.send_message(task_id, "result", data)

    async def send_error(
        self,
        task_id: str,
        error_type: str,
        message: str,
    ) -> None:
        """Send error message to all connections for a task."""
        await self.send_message(
            task_id,
            "error",
            {"error_type": error_type, "message": message},
        )

    async def broadcast_to_task(self, task_id: str, data: dict) -> None:
        """Broadcast custom data to all connections for a task."""
        await self.send_message(task_id, "broadcast", data)


ws_manager = ConnectionManager()

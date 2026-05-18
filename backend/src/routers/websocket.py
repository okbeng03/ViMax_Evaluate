"""WebSocket endpoint for task updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.websocket_manager import ws_manager
from src.utils.logger import logger

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates."""
    await ws_manager.connect(websocket, task_id)
    logger.info(f"WebSocket connection established for task {task_id}", extra={"task_id": task_id})

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message on task {task_id}: {data}", extra={"task_id": task_id})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, task_id)
        logger.info(f"WebSocket disconnected for task {task_id}", extra={"task_id": task_id})

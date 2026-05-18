"""WebSocket integration tests."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket

from src.services.websocket_manager import ConnectionManager


class TestWebSocketManager:
    """Test WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        """Create WebSocket manager."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket."""
        ws = AsyncMock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test WebSocket connection."""
        await manager.connect(mock_websocket, "task-123")
        
        mock_websocket.accept.assert_called_once()
        assert "task-123" in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnection."""
        await manager.connect(mock_websocket, "task-123")
        await manager.disconnect(mock_websocket, "task-123")
        
        assert "task-123" not in manager._connections

    @pytest.mark.asyncio
    async def test_send_message(self, manager, mock_websocket):
        """Test sending WebSocket message."""
        await manager.connect(mock_websocket, "task-123")
        await manager.send_message("task-123", "status", {"status": "processing"})
        
        mock_websocket.send_text.assert_called_once()
        
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert '"type": "status"' in sent_data
        assert '"task_id": "task-123"' in sent_data

    @pytest.mark.asyncio
    async def test_send_status(self, manager, mock_websocket):
        """Test sending status update."""
        await manager.connect(mock_websocket, "task-123")
        await manager.send_status("task-123", "completed", {"progress_percent": 100})
        
        mock_websocket.send_text.assert_called_once()
        
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert '"status": "completed"' in sent_data
        assert '"progress_percent": 100' in sent_data

    @pytest.mark.asyncio
    async def test_send_result(self, manager, mock_websocket):
        """Test sending evaluation result."""
        await manager.connect(mock_websocket, "task-123")
        await manager.send_result(
            "task-123",
            clip_score=0.85,
            clip_interpretation="consistent",
            overall_score=82.0,
            llm_consistency="consistent",
        )
        
        mock_websocket.send_text.assert_called_once()
        
        sent_data = mock_websocket.send_text.call_args[0][0]
        assert '"clip_score": 0.85' in sent_data
        assert '"overall_score": 82.0' in sent_data

    @pytest.mark.asyncio
    async def test_multiple_connections_same_task(self, manager):
        """Test multiple connections for same task."""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        
        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        
        await manager.connect(ws1, "task-123")
        await manager.connect(ws2, "task-123")
        
        await manager.send_message("task-123", "status", {"status": "test"})
        
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_latency(self, manager, mock_websocket):
        """Test WebSocket push latency is under 1 second."""
        import time
        
        await manager.connect(mock_websocket, "task-123")
        
        start = time.time()
        await manager.send_message("task-123", "status", {"status": "processing"})
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"WebSocket latency was {elapsed:.3f}s, expected < 1s"

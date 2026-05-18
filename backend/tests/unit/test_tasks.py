"""Unit tests for task creation."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.schemas import TaskCreate, TaskStatus
from src.services.task_repository import TaskRepository
from src.services.task_manager import TaskManager


class TestTaskCreate:
    """Test task creation validation."""

    def test_task_create_with_url(self):
        """Test task creation with image URL."""
        task = TaskCreate(
            image_url="https://example.com/image.png",
            prompt="A beautiful sunset over the ocean",
        )
        assert task.image_url == "https://example.com/image.png"
        assert task.prompt == "A beautiful sunset over the ocean"

    def test_task_create_with_base64(self):
        """Test task creation with base64 image."""
        task = TaskCreate(
            image_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg==",
            prompt="A cat sitting on a windowsill",
        )
        assert task.image_base64 is not None
        assert task.prompt == "A cat sitting on a windowsill"

    def test_task_create_without_image_raises(self):
        """Test that task creation without image raises error."""
        with pytest.raises(ValueError, match="At least one of image_url or image_base64"):
            TaskCreate(prompt="A beautiful sunset")

    def test_task_create_with_project_id(self):
        """Test task creation with project association."""
        task = TaskCreate(
            image_url="https://example.com/image.png",
            prompt="Test prompt",
            project_id="project-123",
        )
        assert task.project_id == "project-123"


class TestTaskRepository:
    """Test task repository operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_create_task(self, mock_db):
        """Test creating a task."""
        task_data = TaskCreate(
            image_url="https://example.com/image.png",
            prompt="Test prompt",
        )
        
        with patch.object(TaskRepository, "__init__", lambda x, y: None):
            repo = TaskRepository(mock_db)
            repo.db = mock_db
            
            task = MagicMock()
            task.id = "task-123"
            task.project_id = None
            task.image_url = task_data.image_url
            task.image_base64 = None
            task.prompt = task_data.prompt
            task.status = MagicMock()
            task.status.value = "pending"
            task.created_at = datetime.utcnow()
            
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            result = await repo.create_task(task_data)
            
            assert result is not None


class TestTaskManager:
    """Test task manager operations."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_create_task_returns_task_id(self, mock_db_session):
        """Test that task creation returns task_id within acceptable time."""
        import time
        
        task_data = TaskCreate(
            image_url="https://example.com/image.png",
            prompt="Test prompt",
        )
        
        with patch("src.services.task_manager.TaskRepository") as MockRepo, \
             patch("src.services.task_manager.ws_manager") as mock_ws, \
             patch("src.services.task_manager.task_queue") as mock_queue:
            
            mock_task = MagicMock()
            mock_task.id = "task-123"
            mock_task.status = MagicMock()
            mock_task.status.value = "pending"
            mock_task.created_at = datetime.utcnow()
            
            mock_repo = MockRepo.return_value
            mock_repo.create_task = AsyncMock(return_value=mock_task)
            mock_ws.send_status = AsyncMock()
            mock_queue.enqueue = AsyncMock()
            
            manager = TaskManager(mock_db_session)
            manager._repository = mock_repo
            
            start = time.time()
            result = await manager.create_task(task_data)
            elapsed = time.time() - start
            
            assert "task_id" in result
            assert result["task_id"] == "task-123"
            assert elapsed < 5, f"Task creation took {elapsed:.2f}s, expected < 5s"

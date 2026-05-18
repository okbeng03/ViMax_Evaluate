"""Task manager for task lifecycle management."""

from typing import Optional
from datetime import datetime
import asyncio

from src.db.models import TaskStatus, EvaluationResult
from src.models.schemas import TaskCreate, TaskJob, ProgressInfo
from src.services.task_queue import task_queue, TaskJob as QueueTaskJob
from src.services.task_repository import TaskRepository
from src.services.websocket_manager import ws_manager
from src.utils.logger import logger
from src.utils.exceptions import AppException


class TaskManager:
    """Manages task lifecycle and execution."""

    def __init__(self, db_session):
        self._db = db_session
        self._repository = TaskRepository(db_session)

    async def create_task(self, task_data: TaskCreate) -> dict:
        """Create a new evaluation task and enqueue it."""
        task = await self._repository.create_task(task_data)
        
        await ws_manager.send_status(
            task.id,
            str(task.status.value),
            ProgressInfo(
                current_phase="queued",
                phases_completed=[],
                phases_total=2,
                progress_percent=0,
            ).model_dump(),
        )

        job = QueueTaskJob(
            task_id=task.id,
            image_url=task.image_url,
            image_base64=task.image_base64,
            hash_id=task.hash_id,
            prompt=task.prompt,
            project_id=task.project_id,
        )
        await task_queue.enqueue(job)

        logger.info(f"Task created: {task.id}", extra={"task_id": task.id})

        return {
            "task_id": task.id,
            "status": task.status,
            "created_at": task.created_at,
        }

    async def get_task_status(self, task_id: str) -> dict:
        """Get task status."""
        task = await self._repository.get_task_by_id(task_id)
        if not task:
            raise AppException(
                code="TASK_NOT_FOUND",
                message=f"Task {task_id} not found",
            )

        result = await self._repository.get_result_by_task_id(task_id)
        overall_score = result.overall_score if result else None

        return {
            "task_id": task.id,
            "status": task.status,
            "project_id": task.project_id,
            "prompt_summary": task.prompt[:50] + "..." if len(task.prompt) > 50 else task.prompt,
            "overall_score": overall_score,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
        }

    async def get_task_result(self, task_id: str) -> dict:
        """Get task evaluation result."""
        task, result = await self._repository.get_task_with_result(task_id)

        if not task:
            raise AppException(
                code="TASK_NOT_FOUND",
                message=f"Task {task_id} not found",
            )

        if task.status != TaskStatus.COMPLETED or not result:
            raise AppException(
                code="TASK_NOT_COMPLETED",
                message="Task evaluation not yet completed",
                details={"current_status": task.status.value},
            )

        return {
            "task_id": task.id,
            "clip_score": result.clip_score,
            "clip_interpretation": result.clip_interpretation,
            "structured_description": result.structured_description,
            "llm_analysis": result.llm_analysis,
            "llm_consistency": result.llm_consistency,
            "overall_score": result.overall_score,
            "processing_time_ms": result.processing_time_ms,
            "created_at": result.created_at,
        }

    async def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """List tasks with filtering."""
        tasks, total = await self._repository.list_tasks(
            project_id=project_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        task_items = []
        for task in tasks:
            result = await self._repository.get_result_by_task_id(task.id)
            task_items.append({
                "task_id": task.id,
                "status": task.status,
                "project_id": task.project_id,
                "prompt_summary": task.prompt[:50] + "..." if len(task.prompt) > 50 else task.prompt,
                "overall_score": result.overall_score if result else None,
                "created_at": task.created_at,
            })

        return {
            "tasks": task_items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[ProgressInfo] = None,
    ) -> None:
        """Update task status and notify via WebSocket."""
        task = await self._repository.update_task_status(task_id, status)
        if task:
            progress_data = progress.model_dump() if progress else None
            await ws_manager.send_status(
                task_id,
                status.value,
                progress_data,
            )
            logger.info(f"Task {task_id} status updated to {status.value}", extra={"task_id": task_id})

"""Task repository for database operations."""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import EvaluationTask, EvaluationResult, TaskStatus
from src.models.schemas import TaskCreate, TaskStatus as TaskStatusEnum


class TaskRepository:
    """Repository for task database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> EvaluationTask:
        """Create a new evaluation task."""
        task = EvaluationTask(
            project_id=task_data.project_id,
            image_url=task_data.image_url,
            image_base64=task_data.image_base64,
            prompt=task_data.prompt,
            status=TaskStatus.PENDING,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_by_id(self, task_id: str) -> Optional[EvaluationTask]:
        """Get task by ID."""
        result = await self.db.execute(
            select(EvaluationTask).where(EvaluationTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_task_with_result(self, task_id: str) -> Tuple[Optional[EvaluationTask], Optional[EvaluationResult]]:
        """Get task with its result."""
        task_result = await self.db.execute(
            select(EvaluationTask, EvaluationResult)
            .outerjoin(EvaluationResult, EvaluationTask.id == EvaluationResult.task_id)
            .where(EvaluationTask.id == task_id)
        )
        row = task_result.first()
        if row:
            return row[0], row[1]
        return None, None

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        completed_at: Optional[datetime] = None,
    ) -> Optional[EvaluationTask]:
        """Update task status."""
        task = await self.get_task_by_id(task_id)
        if task:
            task.status = status
            if completed_at:
                task.completed_at = completed_at
            await self.db.flush()
            await self.db.refresh(task)
        return task

    async def list_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[EvaluationTask], int]:
        """List tasks with filtering and pagination."""
        conditions = []
        
        if project_id:
            conditions.append(EvaluationTask.project_id == project_id)
        if status:
            conditions.append(EvaluationTask.status == TaskStatus(status))
        if start_date:
            conditions.append(EvaluationTask.created_at >= start_date)
        if end_date:
            conditions.append(EvaluationTask.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        count_result = await self.db.execute(
            select(func.count(EvaluationTask.id)).where(where_clause)
        )
        total = count_result.scalar()

        result = await self.db.execute(
            select(EvaluationTask)
            .where(where_clause)
            .order_by(EvaluationTask.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        tasks = list(result.scalars().all())

        return tasks, total

    async def get_result_by_task_id(self, task_id: str) -> Optional[EvaluationResult]:
        """Get evaluation result by task ID."""
        result = await self.db.execute(
            select(EvaluationResult).where(EvaluationResult.task_id == task_id)
        )
        return result.scalar_one_or_none()

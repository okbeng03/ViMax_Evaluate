"""Task repository for database operations."""

import asyncio
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError

from src.db.models import EvaluationTask, EvaluationResult, TaskStatus
from src.models.schemas import TaskCreate, TaskStatus as TaskStatusEnum
from src.utils.logger import logger

DB_RETRY_COUNT = 3
DB_RETRY_DELAY = 0.5  # seconds


class TaskRepository:
    """Repository for task database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _retry_flush(self, operation_name: str = "flush", re_add=None) -> None:
        """Retry flush on database locked error, then commit to ensure durability.
        
        re_add: optional list of ORM objects to re-add to session after rollback,
                because rollback detaches all objects from the session.
        """
        for attempt in range(DB_RETRY_COUNT):
            try:
                await self.db.flush()
                await self.db.commit()  # 显式提交，确保数据落盘
                return
            except OperationalError as e:
                if "database is locked" in str(e) and attempt < DB_RETRY_COUNT - 1:
                    logger.warning(
                        f"Database locked during {operation_name}, retry {attempt + 1}/{DB_RETRY_COUNT}"
                    )
                    await asyncio.sleep(DB_RETRY_DELAY * (attempt + 1))
                    # 回滚当前失败的事务后重试
                    await self.db.rollback()
                    # rollback 后对象已从 session 分离，需要重新加入
                    if re_add is not None:
                        for obj in re_add:
                            self.db.add(obj)
                    continue
                raise

    async def create_task(self, task_data: TaskCreate) -> EvaluationTask:
        """Create a new evaluation task.
        
        任务先写入数据库并提交，确认持久化后，调用方再将其加入任务队列。
        这样确保入队前数据已可靠存储，避免 database locked 导致的不一致。
        """
        task = EvaluationTask(
            project_id=task_data.project_id,
            image_url=task_data.image_url,
            image_base64=task_data.image_base64,
            hash_id=task_data.hash_id,
            prompt=task_data.prompt,
            status=TaskStatus.PENDING,
        )
        self.db.add(task)
        await self._retry_flush("create_task", re_add=[task])
        # flush+commit 成功后，session 自动开始新事务，refresh 仍可正常工作
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
        """Update task status (flush + commit, with retry on locked)."""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        task.status = status
        if completed_at:
            task.completed_at = completed_at

        for attempt in range(DB_RETRY_COUNT):
            try:
                await self.db.flush()
                await self.db.commit()
                await self.db.refresh(task)
                return task
            except OperationalError as e:
                if "database is locked" in str(e) and attempt < DB_RETRY_COUNT - 1:
                    logger.warning(
                        f"Database locked during update_task_status, retry {attempt + 1}/{DB_RETRY_COUNT}"
                    )
                    await asyncio.sleep(DB_RETRY_DELAY * (attempt + 1))
                    await self.db.rollback()
                    # rollback 后对象已分离，重新查询并应用修改
                    task = await self.get_task_by_id(task_id)
                    if task:
                        task.status = status
                        if completed_at:
                            task.completed_at = completed_at
                    continue
                raise

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

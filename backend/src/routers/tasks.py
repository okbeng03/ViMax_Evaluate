"""Task API endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.schemas import (
    TaskCreate,
    TaskCreateResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskListItem,
    EvaluationResultResponse,
)
from src.services.task_manager import TaskManager
from src.utils.logger import logger

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskCreateResponse:
    """Create a new evaluation task."""
    logger.info("Creating new evaluation task")
    manager = TaskManager(db)
    result = await manager.create_task(task_data)
    return TaskCreateResponse(
        task_id=result["task_id"],
        status=result["status"],
        created_at=result["created_at"],
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskStatusResponse:
    """Get task status by ID."""
    manager = TaskManager(db)
    result = await manager.get_task_status(task_id)
    return TaskStatusResponse(**result)


@router.get("/{task_id}/result", response_model=EvaluationResultResponse)
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResultResponse:
    """Get evaluation result for a task."""
    manager = TaskManager(db)
    result = await manager.get_task_result(task_id)
    return EvaluationResultResponse(**result)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """List tasks with optional filtering and pagination."""
    manager = TaskManager(db)
    result = await manager.list_tasks(
        project_id=project_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return TaskListResponse(**result)

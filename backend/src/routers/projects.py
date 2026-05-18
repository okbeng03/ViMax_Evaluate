"""Project API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.models.schemas import ProjectCreate, ProjectResponse, ProjectWithStats
from src.services.project_service import ProjectService
from src.utils.logger import logger

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new project."""
    logger.info(f"Creating new project: {project_data.name}")
    service = ProjectService(db)
    project = await service.create_project(project_data)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectWithStats:
    """Get project details with statistics."""
    service = ProjectService(db)
    project = await service.get_project_with_stats(project_id)
    if not project:
        from src.utils.exceptions import AppException
        raise AppException(
            code="PROJECT_NOT_FOUND",
            message=f"Project {project_id} not found",
        )
    return project


@router.get("")
async def list_projects(
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all projects with task statistics."""
    service = ProjectService(db)
    projects, total = await service.list_projects(limit=limit, offset=offset)
    return {
        "projects": [p.model_dump() for p in projects],
        "total": total,
    }

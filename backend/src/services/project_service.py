"""Project service for CRUD operations."""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Project, EvaluationTask, EvaluationResult
from src.models.schemas import ProjectCreate, ProjectResponse, ProjectWithStats


class ProjectService:
    """Service for project operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(
            name=project_data.name,
            description=project_data.description,
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[ProjectWithStats], int]:
        """List all projects with task statistics."""
        count_result = await self.db.execute(select(func.count(Project.id)))
        total = count_result.scalar()

        result = await self.db.execute(
            select(Project)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        projects = list(result.scalars().all())

        projects_with_stats = []
        for project in projects:
            stats = await self._get_project_stats(project.id)
            projects_with_stats.append(
                ProjectWithStats(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    task_count=stats["task_count"],
                    avg_score=stats["avg_score"],
                )
            )

        return projects_with_stats, total

    async def get_project_with_stats(self, project_id: str) -> Optional[ProjectWithStats]:
        """Get project with statistics."""
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        stats = await self._get_project_stats(project_id)
        return ProjectWithStats(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=stats["task_count"],
            avg_score=stats["avg_score"],
        )

    async def _get_project_stats(self, project_id: str) -> dict:
        """Get statistics for a project."""
        task_count_result = await self.db.execute(
            select(func.count(EvaluationTask.id))
            .where(EvaluationTask.project_id == project_id)
        )
        task_count = task_count_result.scalar() or 0

        avg_score_result = await self.db.execute(
            select(func.avg(EvaluationResult.overall_score))
            .join(EvaluationTask, EvaluationTask.id == EvaluationResult.task_id)
            .where(
                and_(
                    EvaluationTask.project_id == project_id,
                    EvaluationResult.overall_score.isnot(None),
                )
            )
        )
        avg_score = avg_score_result.scalar()

        return {
            "task_count": task_count,
            "avg_score": round(avg_score, 2) if avg_score else None,
        }

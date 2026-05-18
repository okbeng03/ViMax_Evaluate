"""Health check endpoint for monitoring."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.db.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "Agent图像评估系统",
        "version": "0.1.0",
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Detailed health check with dependency status."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "Agent图像评估系统",
        "version": "0.1.0",
        "dependencies": {
            "database": db_status,
        },
    }

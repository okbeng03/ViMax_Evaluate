"""SQLAlchemy models for Project, EvaluationTask, EvaluationResult."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Integer, Enum
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.db.database import Base


class TaskStatus(str, PyEnum):
    """Task status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClipInterpretation(str, PyEnum):
    """CLIP interpretation values."""
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    AMBIGUOUS = "ambiguous"


class LLMConsistency(str, PyEnum):
    """LLM consistency values."""
    CONSISTENT = "consistent"
    PARTIALLY_CONSISTENT = "partially_consistent"
    INCONSISTENT = "inconsistent"


class Project(Base):
    """Project model for grouping evaluation tasks."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    tasks = relationship("EvaluationTask", back_populates="project")


class EvaluationTask(Base):
    """Evaluation task model."""
    __tablename__ = "evaluation_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    image_url = Column(String(2048), nullable=True)
    image_base64 = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="tasks")
    result = relationship("EvaluationResult", back_populates="task", uselist=False)


class EvaluationResult(Base):
    """Evaluation result model."""
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("evaluation_tasks.id"), unique=True, nullable=False)
    clip_score = Column(Float, nullable=False)
    clip_interpretation = Column(String(50), nullable=False)
    structured_description = Column(Text, nullable=False)
    llm_analysis = Column(Text, nullable=False)
    llm_consistency = Column(String(50), nullable=False)
    overall_score = Column(Float, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    task = relationship("EvaluationTask", back_populates="result")

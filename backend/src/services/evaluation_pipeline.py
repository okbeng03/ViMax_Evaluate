"""Evaluation pipeline orchestrator."""

import asyncio
import time
from typing import Optional

from src.config import settings
from src.db.models import TaskStatus, EvaluationResult, ClipInterpretation
from src.models.schemas import ProgressInfo
from src.services.task_queue import TaskJob
from src.services.clip_evaluator import clip_evaluator
from src.services.comfyui_client import comfyui_client
from src.services.llm_evaluator import llm_evaluator
from src.services.websocket_manager import ws_manager
from src.services.task_repository import TaskRepository
from src.db.database import AsyncSessionLocal
from src.utils.logger import logger


class EvaluationPipeline:
    """Orchestrates the complete evaluation pipeline."""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all evaluator components."""
        if self._initialized:
            return

        try:
            await asyncio.gather(
                clip_evaluator.initialize(),
                comfyui_client.initialize(),
                llm_evaluator.initialize(),
            )
            self._initialized = True
            logger.info("Evaluation pipeline initialized")
        except Exception as e:
            logger.warning(f"Some evaluators failed to initialize: {e}")
            self._initialized = True

    async def process_job(self, job: TaskJob) -> None:
        """Process a single evaluation job."""
        start_time = time.time()
        task_id = job.task_id

        logger.info(f"Starting evaluation for task {task_id}", extra={"task_id": task_id})

        async with AsyncSessionLocal() as db:
            repository = TaskRepository(db)

            try:
                await self._update_status(
                    repository,
                    task_id,
                    TaskStatus.PROCESSING,
                    ProgressInfo(
                        current_phase="clip_evaluation",
                        phases_completed=[],
                        phases_total=2,
                        progress_percent=0,
                    ),
                )

                clip_score, clip_interpretation = await self._run_clip_evaluation(job)
                
                await self._update_status(
                    repository,
                    task_id,
                    TaskStatus.PROCESSING,
                    ProgressInfo(
                        current_phase="llm_evaluation",
                        phases_completed=["clip_evaluation"],
                        phases_total=2,
                        progress_percent=50,
                    ),
                )

                structured_description = await self._run_comfyui_description(job)
                
                llm_consistency, llm_analysis, llm_score = await self._run_llm_evaluation(
                    job.prompt,
                    structured_description,
                )

                overall_score = self._calculate_overall_score(
                    clip_score,
                    llm_score,
                )

                processing_time_ms = int((time.time() - start_time) * 1000)

                await self._save_result(
                    repository,
                    task_id,
                    clip_score,
                    clip_interpretation,
                    structured_description,
                    llm_analysis,
                    llm_consistency,
                    overall_score,
                    processing_time_ms,
                )

                await self._update_status(
                    repository,
                    task_id,
                    TaskStatus.COMPLETED,
                    ProgressInfo(
                        current_phase="completed",
                        phases_completed=["clip_evaluation", "llm_evaluation"],
                        phases_total=2,
                        progress_percent=100,
                    ),
                )

                await ws_manager.send_result(
                    task_id,
                    clip_score,
                    clip_interpretation,
                    overall_score,
                    llm_consistency,
                )

                logger.info(
                    f"Task {task_id} completed: overall_score={overall_score}",
                    extra={"task_id": task_id}
                )

            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}", extra={"task_id": task_id})
                await self._update_status(
                    repository,
                    task_id,
                    TaskStatus.FAILED,
                    None,
                )
                await ws_manager.send_error(
                    task_id,
                    "EVALUATION_FAILED",
                    str(e),
                )

            await db.commit()

    async def _run_clip_evaluation(self, job: TaskJob) -> tuple:
        """Run CLIP evaluation."""
        image_source = job.image_url or job.image_base64
        if not image_source:
            raise ValueError("No image source provided")

        return await clip_evaluator.evaluate(image_source, job.prompt)

    async def _run_comfyui_description(self, job: TaskJob) -> str:
        """Run ComfyUI description generation."""
        image_source = job.image_url or job.image_base64
        if not image_source:
            raise ValueError("No image source provided")

        try:
            return await comfyui_client.generate_description(image_source)
        except Exception as e:
            logger.warning(f"ComfyUI failed, using fallback: {e}")
            return "图片描述生成失败"

    async def _run_llm_evaluation(
        self,
        prompt: str,
        description: str,
    ) -> tuple:
        """Run LLM evaluation."""
        try:
            return await llm_evaluator.evaluate(prompt, description)
        except Exception as e:
            logger.warning(f"LLM evaluation failed, using fallback: {e}")
            return "partially_consistent", "LLM评估失败", 50.0

    def _calculate_overall_score(self, clip_score: float, llm_score: float) -> float:
        """Calculate overall score from CLIP and LLM scores."""
        clip_weight = 0.4
        llm_weight = 0.6
        return round((clip_score * 100 * clip_weight) + (llm_score * llm_weight), 2)

    async def _update_status(
        self,
        repository: TaskRepository,
        task_id: str,
        status: TaskStatus,
        progress: Optional[ProgressInfo],
    ) -> None:
        """Update task status."""
        from datetime import datetime
        completed_at = datetime.utcnow() if status == TaskStatus.COMPLETED else None
        await repository.update_task_status(task_id, status, completed_at)

        progress_data = progress.model_dump() if progress else None
        await ws_manager.send_status(task_id, status.value, progress_data)

    async def _save_result(
        self,
        repository: TaskRepository,
        task_id: str,
        clip_score: float,
        clip_interpretation: str,
        structured_description: str,
        llm_analysis: str,
        llm_consistency: str,
        overall_score: float,
        processing_time_ms: int,
    ) -> None:
        """Save evaluation result."""
        from datetime import datetime
        from sqlalchemy import select
        from src.db.models import EvaluationResult as EvaluationResultModel

        result = EvaluationResultModel(
            task_id=task_id,
            clip_score=clip_score,
            clip_interpretation=clip_interpretation,
            structured_description=structured_description,
            llm_analysis=llm_analysis,
            llm_consistency=llm_consistency,
            overall_score=overall_score,
            processing_time_ms=processing_time_ms,
        )
        repository.db.add(result)


evaluation_pipeline = EvaluationPipeline()

"""Evaluation pipeline orchestrator."""

import asyncio
import json
import time
from typing import Optional

from src.config import settings
from src.db.models import TaskStatus, EvaluationResult, ClipInterpretation
from src.models.schemas import ProgressInfo
from src.services.task_queue import TaskJob
from src.services.clip_evaluator import clip_evaluator
from src.services.comfyui_client import comfyui_client
from src.services.llm_evaluator import llm_evaluator, LLMConsistencyResult
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
                        progress_percent=30,
                    ),
                )

                structured_description = await self._run_comfyui_description(job)
                # structured_description = "zzz"
                
                llm_result = await self._run_llm_evaluation(
                    job.prompt,
                    structured_description,
                )

                overall_score = self._calculate_overall_score(
                    clip_score,
                    llm_result.overall_score,
                )

                processing_time_ms = int((time.time() - start_time) * 1000)

                await self._save_result(
                    repository,
                    task_id,
                    clip_score,
                    clip_interpretation,
                    structured_description,
                    llm_result,
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
                    llm_result.consistency,
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

    def _get_image_source(self, job: TaskJob) -> str:
        """Get image source from job, checking url, base64, or hash_id."""
        image_source = job.image_url or job.image_base64 or job.hash_id
        if not image_source:
            raise ValueError("No image source provided (url, base64, or hash_id)")
        return image_source

    async def _run_clip_evaluation(self, job: TaskJob) -> tuple:
        """Run CLIP evaluation."""
        image_source = self._get_image_source(job)
        return await clip_evaluator.evaluate(image_source, job.prompt)

    async def _run_comfyui_description(self, job: TaskJob) -> str:
        """Run ComfyUI description generation."""
        image_source = self._get_image_source(job)

        try:
            return await comfyui_client.generate_description(image_source)
        except Exception as e:
            logger.warning(f"ComfyUI failed, using fallback: {e}")
            return "图片描述生成失败"

    async def _run_llm_evaluation(
        self,
        prompt: str,
        description: str,
    ) -> LLMConsistencyResult:
        """Run LLM evaluation."""
        try:
            return await llm_evaluator.evaluate(prompt, description)
        except Exception as e:
            logger.warning(f"LLM evaluation failed, using fallback: {e}")
            # 返回 fallback 结果
            from src.services.llm_evaluator import DimensionScore
            return LLMConsistencyResult(
                consistency="partially_consistent",
                overall_score=50.0,
                dimension_scores=DimensionScore(
                    subject_consistency=50.0, action_consistency=50.0,
                    attribute_consistency=50.0, spatial_consistency=50.0,
                    composition_consistency=50.0, lighting_consistency=50.0,
                    style_consistency=50.0, anatomy_quality=50.0, artifact_quality=50.0
                ),
                matched_requirements=[],
                missing_requirements=[],
                incorrect_requirements=[],
                extra_elements=[],
                critical_failures=[f"LLM evaluation failed: {str(e)}"],
                analysis="LLM评估失败"
            )

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
        llm_result: LLMConsistencyResult,
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
            llm_analysis=llm_result.analysis,
            llm_consistency=llm_result.consistency,
            overall_score=overall_score,
            processing_time_ms=processing_time_ms,
            # 扩展 LLM 评估结果
            llm_overall_score=llm_result.overall_score,
            llm_dimension_scores=llm_result.dimension_scores.model_dump(),
            llm_matched_requirements=[r.model_dump() for r in llm_result.matched_requirements],
            llm_missing_requirements=[r.model_dump() for r in llm_result.missing_requirements],
            llm_incorrect_requirements=[r.model_dump() for r in llm_result.incorrect_requirements],
            llm_extra_elements=llm_result.extra_elements,
            llm_critical_failures=llm_result.critical_failures,
        )
        repository.db.add(result)


evaluation_pipeline = EvaluationPipeline()

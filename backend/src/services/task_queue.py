"""Async task queue for evaluation jobs."""

import asyncio
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import logger


@dataclass
class TaskJob:
    """Task job data structure."""
    task_id: str
    image_url: Optional[str]
    image_base64: Optional[str]
    prompt: str
    project_id: Optional[str] = None


class TaskQueue:
    """Async task queue using asyncio.Queue."""

    def __init__(self, max_size: int = 100):
        self._queue: asyncio.Queue[TaskJob] = asyncio.Queue(maxsize=max_size)
        self._processing = set()
        self._handler: Optional[Callable[[TaskJob], Awaitable[None]]] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, handler: Callable[[TaskJob], Awaitable[None]]) -> None:
        """Start the task queue worker."""
        if self._running:
            return

        self._handler = handler
        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        logger.info("Task queue worker started")

    async def stop(self) -> None:
        """Stop the task queue worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Task queue worker stopped")

    async def enqueue(self, job: TaskJob) -> None:
        """Add a job to the queue."""
        await self._queue.put(job)
        logger.info(f"Task {job.task_id} enqueued", extra={"task_id": job.task_id})

    async def _process_queue(self) -> None:
        """Process jobs from the queue."""
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            self._processing.add(job.task_id)
            logger.info(f"Processing task {job.task_id}", extra={"task_id": job.task_id})

            try:
                if self._handler:
                    await self._handler(job)
            except Exception as e:
                logger.error(f"Task {job.task_id} failed: {e}", extra={"task_id": job.task_id})
            finally:
                self._processing.discard(job.task_id)
                self._queue.task_done()

    @property
    def size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def processing_count(self) -> int:
        """Get number of tasks currently processing."""
        return len(self._processing)


task_queue = TaskQueue()

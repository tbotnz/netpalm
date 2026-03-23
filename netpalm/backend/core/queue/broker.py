"""
QueueBroker — transactional outbox pattern.

Writes jobs to PostgreSQL with status=pending.
The Scheduler service handles Kafka publishing.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.models.db_models import JobRecord

log = logging.getLogger(__name__)


class TaskNotFoundError(Exception):
    """Raised when a task_id does not exist in the jobs table."""


class TaskResponse:
    """Lightweight response returned immediately after job submission."""

    def __init__(
        self,
        task_id: uuid.UUID,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error

    def model_dump(self) -> dict[str, Any]:
        return {
            "task_id": str(self.task_id),
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class QueueBroker:
    """
    Writes jobs to the DB (outbox pattern).
    Never calls Kafka directly — that is the Scheduler's responsibility.
    """

    def __init__(self, db: AsyncSession, settings: NetpalmSettings) -> None:
        self._db = db
        self._settings = settings

    async def enqueue_task(
        self,
        method: str,
        kwargs: dict[str, Any],
        queue_strategy: str = "fifo",
        pinned_host: str | None = None,
        task_id: uuid.UUID | None = None,
    ) -> TaskResponse:
        """
        INSERT a JobRecord with status=pending.
        Returns immediately — does NOT wait for Kafka publish.
        """
        if task_id is None:
            task_id = uuid.uuid4()

        job = JobRecord(
            task_id=task_id,
            method=method,
            queue_strategy=queue_strategy,
            pinned_host=pinned_host,
            status="pending",
            payload=kwargs,
        )
        self._db.add(job)
        await self._db.commit()
        log.debug(f"enqueue_task: inserted job {task_id} method={method} strategy={queue_strategy}")
        return TaskResponse(task_id=task_id, status="pending")

    async def fetch_task(self, task_id: str | uuid.UUID) -> TaskResponse:
        """SELECT job row from DB and return as TaskResponse."""
        if isinstance(task_id, str):
            task_id = uuid.UUID(task_id)

        result = await self._db.execute(select(JobRecord).where(JobRecord.task_id == task_id))
        job: JobRecord | None = result.scalar_one_or_none()
        if job is None:
            raise TaskNotFoundError(f"task {task_id} not found")

        return TaskResponse(
            task_id=job.task_id,
            status=job.status,
            result=job.result,
            error=job.error,
        )

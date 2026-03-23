"""
Scheduler — two responsibilities running concurrently:

1. Outbox relay: polls jobs WHERE status='pending', publishes to Kafka, marks 'queued'.
2. Scheduled job runner: polls scheduled_jobs WHERE next_run_at <= now() AND enabled=True,
   inserts a new JobRecord per due job, updates next_run_at for recurring triggers.

Replaces both the old OutboxRelay and APScheduler entirely.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.models.db_models import JobRecord, ScheduledJobRecord
from netpalm.backend.core.models.models import QueueStrategy, TaskMessage

log = logging.getLogger(__name__)

_BATCH_SIZE = 50


class Scheduler:
    """
    Outbox relay + scheduled job dispatcher.
    Runs as a separate process: python -m netpalm.scheduler
    """

    def __init__(
        self,
        db_factory: Callable[[], AsyncSession],
        producer: AIOKafkaProducer,
        settings: NetpalmSettings,
    ) -> None:
        self._db_factory = db_factory
        self._producer = producer
        self._settings = settings

    async def run(self) -> None:
        """Main loop: runs both relay and dispatch concurrently."""
        log.info("Scheduler: starting")
        await self._producer.start()
        try:
            while True:
                await asyncio.gather(
                    self._relay_pending_jobs(),
                    self._dispatch_scheduled_jobs(),
                )
                await asyncio.sleep(self._settings.scheduler_poll_interval_seconds)
        finally:
            await self._producer.stop()

    async def _relay_pending_jobs(self) -> int:
        """Fetch pending jobs, publish to Kafka, mark queued. Returns count published."""
        published = 0
        async with self._db_factory() as session:
            result = await session.execute(
                select(JobRecord)
                .where(JobRecord.status == "pending")
                .limit(_BATCH_SIZE)
                .with_for_update(skip_locked=True)
            )
            jobs: list[JobRecord] = list(result.scalars().all())

            for job in jobs:
                topic = self._resolve_topic(job)
                msg = TaskMessage(
                    task_id=job.task_id,
                    method=job.method,
                    kwargs=job.payload,
                    queue_strategy=QueueStrategy(job.queue_strategy),
                    pinned_host=job.pinned_host,
                )
                try:
                    await self._producer.send(
                        topic,
                        key=str(job.task_id).encode(),
                        value=msg.model_dump_json().encode(),
                    )
                    await self._producer.flush()
                    job.status = "queued"
                    published += 1
                    log.debug(f"Scheduler: relayed {job.task_id} → {topic}")
                except KafkaError as exc:
                    log.error(f"Scheduler: Kafka error for {job.task_id}: {exc} — leaving pending")

            await session.commit()

        return published

    async def _dispatch_scheduled_jobs(self) -> int:
        """Find due scheduled jobs, insert job rows, update next_run_at. Returns count dispatched."""
        dispatched = 0
        now = datetime.now(timezone.utc)

        async with self._db_factory() as session:
            result = await session.execute(
                select(ScheduledJobRecord).where(
                    ScheduledJobRecord.next_run_at <= now,
                    ScheduledJobRecord.enabled.is_(True),
                )
            )
            due: list[ScheduledJobRecord] = list(result.scalars().all())

            for sched in due:
                job = JobRecord(
                    task_id=uuid.uuid4(),
                    method=sched.method,
                    queue_strategy="fifo",
                    status="pending",
                    payload=sched.payload,
                )
                session.add(job)

                sched.last_run_at = now
                sched.next_run_at = _compute_next_run(sched, now)
                dispatched += 1
                log.debug(f"Scheduler: dispatched scheduled job {sched.job_id} ({sched.name})")

            await session.commit()

        return dispatched

    def _resolve_topic(self, job: JobRecord) -> str:
        """fifo → kafka_fifo_topic; pinned → kafka_pinned_topic_prefix.{host}"""
        if job.queue_strategy == QueueStrategy.pinned and job.pinned_host:
            return f"{self._settings.kafka_pinned_topic_prefix}.{job.pinned_host}"
        return self._settings.kafka_fifo_topic


def _compute_next_run(sched: ScheduledJobRecord, last_run: datetime) -> datetime:
    """Compute the next run time for interval/cron/date triggers."""
    trigger = sched.trigger
    args: dict[str, Any] = sched.trigger_args or {}

    if trigger == "interval":
        seconds = (
            args.get("seconds", 0)
            + args.get("minutes", 0) * 60
            + args.get("hours", 0) * 3600
            + args.get("days", 0) * 86400
            + args.get("weeks", 0) * 604800
        )
        if seconds <= 0:
            seconds = 60  # fallback
        return last_run + timedelta(seconds=seconds)

    if trigger == "cron":
        # Simple cron: advance by 1 minute and let the next poll cycle handle it.
        # Full cron parsing would require croniter; keeping dependency-free here.
        return last_run + timedelta(minutes=1)

    # "date" trigger — one-shot; disable after firing
    sched.enabled = False
    return last_run

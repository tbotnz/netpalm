"""
NetpalmExecutor — Kafka consumer that executes driver tasks and writes results to PostgreSQL.

Subscribes to:
  - Job topics (fifo + pinned) from DriverRegistry
  - Event topics from EventListenerRegistry

For each job message:
  1. UPDATE job status → started
  2. Look up driver via DriverRegistry
  3. Execute driver.connect() / sendcommand() or config()
  4. UPDATE job status → finished (or failed)
  5. Produce ResultMessage to netpalm.results
"""
from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from netpalm.backend.core.confload.confload import NetpalmSettings
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.events.registry import EventListenerRegistry
from netpalm.backend.core.models.db_models import JobRecord
from netpalm.backend.core.models.models import ResultMessage, TaskMessage

log = logging.getLogger(__name__)


class NetpalmExecutor:
    """
    Kafka consumer that executes driver tasks and dispatches event messages.
    """

    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        producer: AIOKafkaProducer,
        db_factory: Callable[[], AsyncSession],
        driver_registry: DriverRegistry,
        event_registry: EventListenerRegistry,
        settings: NetpalmSettings,
    ) -> None:
        self._consumer = consumer
        self._producer = producer
        self._db_factory = db_factory
        self._driver_registry = driver_registry
        self._event_registry = event_registry
        self._settings = settings

    async def run(self) -> None:
        """Main consume loop. Runs until cancelled."""
        job_topics = [
            self._settings.kafka_fifo_topic,
        ]
        event_topics = self._event_registry.get_topics()
        all_topics = list(set(job_topics + event_topics))

        self._consumer.subscribe(all_topics)
        await self._consumer.start()
        await self._producer.start()
        log.info(f"NetpalmExecutor: subscribed to {all_topics}")

        try:
            async for msg in self._consumer:
                topic: str = msg.topic
                raw: bytes = msg.value

                if topic in event_topics:
                    await self._event_registry.dispatch(topic, raw)
                else:
                    try:
                        task_msg = TaskMessage.model_validate_json(raw)
                        await self._handle_task(task_msg)
                    except Exception as exc:
                        log.error(f"NetpalmExecutor: failed to parse task message: {exc}")
        finally:
            await self._consumer.stop()
            await self._producer.stop()

    async def _handle_task(self, msg: TaskMessage) -> None:
        """Execute driver call, write result to DB and results topic."""
        task_id = msg.task_id
        log.info(f"NetpalmExecutor: handling task {task_id} method={msg.method}")

        async with self._db_factory() as session:
            # Mark started
            result = await session.execute(
                select(JobRecord).where(JobRecord.task_id == task_id)
            )
            job: JobRecord | None = result.scalar_one_or_none()
            if job is None:
                log.error(f"NetpalmExecutor: job {task_id} not found in DB")
                return

            job.status = "started"
            job.started_at = datetime.now(timezone.utc)
            await session.commit()

        # Execute driver
        task_result: dict[str, Any] | None = None
        task_error: str | None = None

        try:
            driver_cls = self._driver_registry.get(msg.kwargs.get("library", ""))
            driver = driver_cls(**msg.kwargs)
            session_obj = driver.connect()
            command = msg.kwargs.get("command") or msg.kwargs.get("config")
            if msg.method == "getconfig":
                task_result = driver.sendcommand(session_obj, command if isinstance(command, list) else [command])
            else:
                task_result = driver.config(session_obj, command)
            driver.logout(session_obj)
            final_status = "finished"
        except Exception as exc:
            log.error(f"NetpalmExecutor: task {task_id} failed: {exc}")
            task_error = str(exc)
            final_status = "failed"

        # Write result
        async with self._db_factory() as session:
            result = await session.execute(
                select(JobRecord).where(JobRecord.task_id == task_id)
            )
            job = result.scalar_one_or_none()
            if job:
                job.status = final_status
                job.result = task_result
                job.error = task_error
                job.ended_at = datetime.now(timezone.utc)
                await session.commit()

        # Produce result message
        result_msg = ResultMessage(
            task_id=task_id,
            status=final_status,
            result=task_result,
            error=task_error,
        )
        try:
            await self._producer.send(
                self._settings.kafka_results_topic,
                key=str(task_id).encode(),
                value=result_msg.model_dump_json().encode(),
            )
        except Exception as exc:
            log.error(f"NetpalmExecutor: failed to produce result for {task_id}: {exc}")

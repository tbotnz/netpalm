"""
netpalm.scheduler — entry-point for the Scheduler service.

Run with:
    python -m netpalm.scheduler
"""
from __future__ import annotations

import asyncio
import logging

from aiokafka import AIOKafkaProducer

from netpalm.backend.core.confload.confload import get_settings
from netpalm.backend.core.db import get_session_factory
from netpalm.backend.core.scheduler.scheduler import Scheduler

log = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    settings.setup_logging()

    session_factory = get_session_factory()
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)

    scheduler = Scheduler(
        db_factory=session_factory,
        producer=producer,
        settings=settings,
    )
    await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())

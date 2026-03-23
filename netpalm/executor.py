"""
netpalm.executor — entry-point for the Executor (Kafka consumer) service.

Run with:
    python -m netpalm.executor
"""
from __future__ import annotations

import asyncio
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from netpalm.backend.core.cache.store import CacheStore
from netpalm.backend.core.confload.confload import get_settings
from netpalm.backend.core.db import get_session_factory
from netpalm.backend.core.driver.driver_auto_loader import DriverRegistry
from netpalm.backend.core.events.registry import EventListenerRegistry
from netpalm.backend.core.executor.executor import NetpalmExecutor
from netpalm.backend.core.manager.netpalm_manager import NetpalmManager
from netpalm.backend.core.queue.broker import QueueBroker
from netpalm.backend.core.service.store import ServiceStore

log = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    settings.setup_logging()

    session_factory = get_session_factory()

    # Build a manager for EventListeners to call back into
    async with session_factory() as session:
        broker = QueueBroker(db=session, settings=settings)
        service_store = ServiceStore(db=session)
        cache = CacheStore(settings=settings)
        manager = NetpalmManager(
            broker=broker,
            service_store=service_store,
            cache=cache,
            settings=settings,
        )

    driver_registry = DriverRegistry(settings=settings)
    driver_registry.load()

    event_registry = EventListenerRegistry(manager=manager, settings=settings)
    event_registry.load()

    consumer = AIOKafkaConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)

    executor = NetpalmExecutor(
        consumer=consumer,
        producer=producer,
        db_factory=session_factory,
        driver_registry=driver_registry,
        event_registry=event_registry,
        settings=settings,
    )
    await executor.run()


if __name__ == "__main__":
    asyncio.run(main())

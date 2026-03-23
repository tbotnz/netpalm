"""
Manager module — provides a FastAPI-compatible dependency factory
and a legacy module-level singleton for backward compat with existing routers.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from netpalm.backend.core.cache.store import CacheStore
from netpalm.backend.core.confload.confload import NetpalmSettings, get_settings
from netpalm.backend.core.db import get_db_session
from netpalm.backend.core.manager.netpalm_manager import NetpalmManager
from netpalm.backend.core.queue.broker import QueueBroker
from netpalm.backend.core.service.store import ServiceStore


async def get_manager(
    session: AsyncSession = Depends(get_db_session),
    settings: NetpalmSettings = Depends(get_settings),
) -> NetpalmManager:
    """FastAPI dependency that yields a fully-wired NetpalmManager."""
    broker = QueueBroker(db=session, settings=settings)
    service_store = ServiceStore(db=session)
    cache = CacheStore(settings=settings)
    return NetpalmManager(
        broker=broker,
        service_store=service_store,
        cache=cache,
        settings=settings,
    )

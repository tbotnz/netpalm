"""
NetpalmManager — orchestration layer.

Translates typed request models into DB-backed job records via QueueBroker,
reads results from the DB, and manages service instance lifecycle via ServiceStore.

No direct Kafka, Redis, or raw DB access — delegates to injected dependencies.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.cache.store import CacheStore
from netpalm.backend.core.confload.confload import NetpalmSettings, get_settings
from netpalm.backend.core.models.models import (
    GetConfig,
    NetpalmEvent,
    QueueStrategy,
    Script,
    ServiceInstanceData,
    ServiceTaskResponse,
    ServiceVersionSummary,
    SetConfig,
    TaskResponse,
)
from netpalm.backend.core.queue.broker import QueueBroker, TaskNotFoundError
from netpalm.backend.core.queue.broker import TaskResponse as BrokerTaskResponse
from netpalm.backend.core.service.state_machine import ServiceInstanceState
from netpalm.backend.core.service.store import ServiceStore

log = logging.getLogger(__name__)


class NetpalmManager:
    """
    Orchestration layer — no direct Kafka/Redis/DB access.
    All persistence goes through QueueBroker and ServiceStore.
    """

    def __init__(
        self,
        broker: QueueBroker,
        service_store: ServiceStore,
        cache: CacheStore,
        settings: NetpalmSettings | None = None,
    ) -> None:
        self._broker = broker
        self._service_store = service_store
        self._cache = cache
        self._settings = settings or get_settings()

    # ── task operations ───────────────────────────────────────────────────────

    async def get_config(self, request: GetConfig) -> dict[str, Any]:
        """
        Enqueue a getconfig job.
        If cache is enabled and a result exists, return it without enqueuing.
        """
        req_data = request.model_dump(exclude_none=True)
        conn = req_data.get("connection_args", {})
        host = conn.get("host", "")
        port = conn.get("port", "")
        cache_key = f"{host}:{port}:{req_data.get('command', '')}"

        if self._settings.redis_cache_enabled and not req_data.get("cache", {}).get("poison"):
            cached = self._cache.get(cache_key)
            if cached is not None:
                log.debug(f"NetpalmManager.get_config: cache hit for {cache_key}")
                return cached

        strategy = req_data.get("queue_strategy", QueueStrategy.fifo)
        pinned_host = host if strategy == QueueStrategy.pinned else None

        task = await self._broker.enqueue_task(
            method="getconfig",
            kwargs=req_data,
            queue_strategy=str(strategy),
            pinned_host=pinned_host,
        )
        return _task_to_response(task)

    async def set_config(self, request: SetConfig) -> dict[str, Any]:
        req_data = request.model_dump(exclude_none=True)
        conn = req_data.get("connection_args", {})
        host = conn.get("host", "")
        strategy = req_data.get("queue_strategy", QueueStrategy.fifo)
        pinned_host = host if strategy == QueueStrategy.pinned else None

        # poison cache on set
        if host:
            self._cache.poison(f"{host}:")

        task = await self._broker.enqueue_task(
            method="setconfig",
            kwargs=req_data,
            queue_strategy=str(strategy),
            pinned_host=pinned_host,
        )
        return _task_to_response(task)

    async def execute_script(self, request: Script) -> dict[str, Any]:
        req_data = request.model_dump(exclude_none=True)
        strategy = req_data.get("queue_strategy", QueueStrategy.fifo)
        pinned_host = req_data.get("script") if strategy == QueueStrategy.pinned else None

        task = await self._broker.enqueue_task(
            method="script",
            kwargs=req_data,
            queue_strategy=str(strategy),
            pinned_host=pinned_host,
        )
        return _task_to_response(task)

    async def fetch_task(self, task_id: str) -> dict[str, Any]:
        task = await self._broker.fetch_task(task_id)
        return _task_to_response(task)

    # ── service operations ────────────────────────────────────────────────────

    async def create_service(self, model: str, request: Any) -> dict[str, Any]:
        if isinstance(request, dict):
            req_data = request
        else:
            req_data = request.model_dump(exclude_none=True)

        service_id = uuid.uuid4()
        await self._service_store.create(service_id=service_id, model=model, data=req_data)

        task = await self._broker.enqueue_task(
            method="service_create",
            kwargs={"service_id": str(service_id), "service_model": model, "data": req_data},
            queue_strategy="fifo",
            task_id=uuid.uuid4(),
        )
        return {
            "status": "success",
            "data": {
                "service_id": str(service_id),
                "task_id": str(task.task_id),
                "status": task.status,
            },
        }

    async def get_service(self, service_id: str) -> dict[str, Any]:
        instance = await self._service_store.fetch(service_id)
        return {
            "status": "success",
            "data": jsonable_encoder(instance),
        }

    async def update_service(self, service_id: str, request: Any) -> dict[str, Any]:
        if isinstance(request, dict):
            req_data = request
        else:
            req_data = request.model_dump(exclude_none=True)

        instance = await self._service_store.update_data(service_id, req_data)

        task = await self._broker.enqueue_task(
            method="service_update",
            kwargs={"service_id": service_id, "data": req_data},
            queue_strategy="fifo",
        )
        return {
            "status": "success",
            "data": {
                "service_id": service_id,
                "task_id": str(task.task_id),
                "status": task.status,
            },
        }

    async def delete_service(self, service_id: str) -> dict[str, Any]:
        await self._service_store.delete(service_id)

        task = await self._broker.enqueue_task(
            method="service_delete",
            kwargs={"service_id": service_id},
            queue_strategy="fifo",
        )
        return _task_to_response(task)

    async def list_services(self) -> dict[str, Any]:
        instances = await self._service_store.list_all()
        return {
            "status": "success",
            "data": {"task_result": [jsonable_encoder(i) for i in instances]},
        }

    async def list_service_versions(self, service_id: str) -> dict[str, Any]:
        versions = await self._service_store.list_versions(service_id)
        return {
            "status": "success",
            "data": {"versions": [jsonable_encoder(v) for v in versions]},
        }

    async def rollback_service(
        self, service_id: str, to_version: int | None = None
    ) -> dict[str, Any]:
        instance = await self._service_store.rollback(service_id, to_version)
        return {
            "status": "success",
            "data": jsonable_encoder(instance),
        }


# ── helpers ───────────────────────────────────────────────────────────────────

def _task_to_response(task: BrokerTaskResponse) -> dict[str, Any]:
    return {
        "status": "success",
        "data": {
            "task_id": str(task.task_id),
            "task_status": task.status,
            "task_result": task.result,
            "task_errors": [task.error] if task.error else [],
        },
    }

"""
ServiceStore — CRUD for service instances backed by PostgreSQL.

Enforces state machine transitions, takes version snapshots before
every mutating transition, and auto-rolls back on updating→errored.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from netpalm.backend.core.models.db_models import (
    JobRecord,
    ServiceInstanceRecord,
    ServiceInstanceVersionRecord,
)
from netpalm.backend.core.models.models import ServiceInstanceData, ServiceVersionSummary
from netpalm.backend.core.service.state_machine import (
    VALID_TRANSITIONS,
    InvalidStateTransitionError,
    ServiceInstanceState,
    ServiceVersionNotFoundError,
    validate_transition,
)

log = logging.getLogger(__name__)

# Transitions that mutate data and therefore require a snapshot first
_SNAPSHOT_BEFORE: set[tuple[ServiceInstanceState, ServiceInstanceState]] = {
    (ServiceInstanceState.deploying, ServiceInstanceState.deployed),
    (ServiceInstanceState.deployed, ServiceInstanceState.updating),
    (ServiceInstanceState.updating, ServiceInstanceState.deployed),
}


class ServiceNotFoundError(Exception):
    def __init__(self, service_id: str) -> None:
        super().__init__(f"Service {service_id} not found")


class ServiceStore:
    """Service instance persistence with state machine enforcement."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _get_record(self, service_id: str | uuid.UUID) -> ServiceInstanceRecord:
        if isinstance(service_id, str):
            service_id = uuid.UUID(service_id)
        result = await self._db.execute(
            select(ServiceInstanceRecord).where(
                ServiceInstanceRecord.service_id == service_id
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise ServiceNotFoundError(str(service_id))
        return record

    def _to_data(self, record: ServiceInstanceRecord) -> ServiceInstanceData:
        return ServiceInstanceData(
            service_id=record.service_id,
            service_model=record.service_model,
            state=record.state,
            data=record.data,
            created_at=record.created_at,
            updated_at=record.updated_at,
            current_version=record.current_version,
        )

    # ── public API ────────────────────────────────────────────────────────────

    async def create(
        self,
        service_id: str | uuid.UUID | None,
        model: str,
        data: dict[str, Any],
    ) -> ServiceInstanceData:
        """INSERT service_instances with state=deploying."""
        if service_id is None:
            service_id = uuid.uuid4()
        elif isinstance(service_id, str):
            service_id = uuid.UUID(service_id)

        record = ServiceInstanceRecord(
            service_id=service_id,
            service_model=model,
            state=ServiceInstanceState.deploying.value,
            data=data,
            current_version=0,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        log.debug(f"ServiceStore.create: {service_id} model={model}")
        return self._to_data(record)

    async def fetch(self, service_id: str | uuid.UUID) -> ServiceInstanceData:
        """SELECT service instance; raises ServiceNotFoundError if missing."""
        record = await self._get_record(service_id)
        return self._to_data(record)

    async def transition(
        self,
        service_id: str | uuid.UUID,
        new_state: ServiceInstanceState,
    ) -> None:
        """
        Validate transition is allowed, take snapshot if required,
        then UPDATE state. Auto-rollback on updating→errored.
        """
        record = await self._get_record(service_id)
        current = ServiceInstanceState(record.state)
        validate_transition(current, new_state)

        # snapshot before mutating transitions
        if (current, new_state) in _SNAPSHOT_BEFORE:
            await self._snapshot_record(record)

        record.state = new_state.value
        record.updated_at = datetime.now(timezone.utc)
        await self._db.commit()

        # auto-rollback when update fails
        if current == ServiceInstanceState.updating and new_state == ServiceInstanceState.errored:
            log.warning(f"ServiceStore: updating→errored for {service_id}, triggering rollback")
            await self.rollback(service_id)

    async def update_data(
        self,
        service_id: str | uuid.UUID,
        data: dict[str, Any],
    ) -> ServiceInstanceData:
        """Transition deployed→updating and persist new data."""
        record = await self._get_record(service_id)
        current = ServiceInstanceState(record.state)
        validate_transition(current, ServiceInstanceState.updating)

        await self._snapshot_record(record)
        record.state = ServiceInstanceState.updating.value
        record.data = data
        record.updated_at = datetime.now(timezone.utc)
        await self._db.commit()
        await self._db.refresh(record)
        return self._to_data(record)

    async def delete(self, service_id: str | uuid.UUID) -> None:
        """Transition to deleting."""
        await self.transition(service_id, ServiceInstanceState.deleting)

    async def list_all(self) -> list[ServiceInstanceData]:
        """SELECT all non-deleted service instances."""
        result = await self._db.execute(
            select(ServiceInstanceRecord).where(
                ServiceInstanceRecord.state != ServiceInstanceState.deleted.value
            )
        )
        return [self._to_data(r) for r in result.scalars().all()]

    async def snapshot(self, service_id: str | uuid.UUID) -> int:
        """
        Write current state+data to service_instance_versions, increment version.
        Returns the new version number.
        """
        record = await self._get_record(service_id)
        return await self._snapshot_record(record)

    async def _snapshot_record(self, record: ServiceInstanceRecord) -> int:
        new_version = record.current_version + 1
        snap = ServiceInstanceVersionRecord(
            version_id=uuid.uuid4(),
            service_id=record.service_id,
            version=new_version,
            state=record.state,
            data=record.data,
        )
        self._db.add(snap)
        record.current_version = new_version
        await self._db.flush()
        log.debug(f"ServiceStore.snapshot: {record.service_id} v{new_version}")
        return new_version

    async def rollback(
        self,
        service_id: str | uuid.UUID,
        to_version: int | None = None,
    ) -> ServiceInstanceData:
        """
        Restore state+data from a version snapshot.
        Enqueues a service_rollback job.
        """
        record = await self._get_record(service_id)

        if to_version is not None:
            result = await self._db.execute(
                select(ServiceInstanceVersionRecord).where(
                    ServiceInstanceVersionRecord.service_id == record.service_id,
                    ServiceInstanceVersionRecord.version == to_version,
                )
            )
            snap = result.scalar_one_or_none()
            if snap is None:
                raise ServiceVersionNotFoundError(str(service_id), to_version)
        else:
            # most recent previous version
            result = await self._db.execute(
                select(ServiceInstanceVersionRecord)
                .where(ServiceInstanceVersionRecord.service_id == record.service_id)
                .order_by(ServiceInstanceVersionRecord.version.desc())
                .limit(1)
            )
            snap = result.scalar_one_or_none()
            if snap is None:
                raise ServiceVersionNotFoundError(str(service_id), -1)

        record.state = ServiceInstanceState.deploying.value
        record.data = snap.data
        record.updated_at = datetime.now(timezone.utc)

        # enqueue rollback job
        rollback_job = JobRecord(
            task_id=uuid.uuid4(),
            method="service_rollback",
            queue_strategy="fifo",
            status="pending",
            payload={
                "service_id": str(record.service_id),
                "service_model": record.service_model,
                "data": snap.data,
                "rollback_to_version": snap.version,
            },
        )
        self._db.add(rollback_job)
        await self._db.commit()
        await self._db.refresh(record)
        log.info(f"ServiceStore.rollback: {service_id} → v{snap.version}")
        return self._to_data(record)

    async def list_versions(
        self, service_id: str | uuid.UUID
    ) -> list[ServiceVersionSummary]:
        """Return all version snapshots ordered by version desc."""
        if isinstance(service_id, str):
            service_id = uuid.UUID(service_id)
        result = await self._db.execute(
            select(ServiceInstanceVersionRecord)
            .where(ServiceInstanceVersionRecord.service_id == service_id)
            .order_by(ServiceInstanceVersionRecord.version.desc())
        )
        return [
            ServiceVersionSummary(
                version_id=r.version_id,
                service_id=r.service_id,
                version=r.version,
                state=r.state,
                created_at=r.created_at,
            )
            for r in result.scalars().all()
        ]

"""
schedule routes — CRUD for scheduled jobs backed by PostgreSQL.

APScheduler has been removed. Scheduled jobs are stored in the
`scheduled_jobs` table and dispatched by the Scheduler service.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from netpalm.backend.core.db import get_db_session
from netpalm.backend.core.models.db_models import ScheduledJobRecord
from netpalm.backend.core.models.models import ScheduleBase, ScheduleInterval
from netpalm.routers.route_utils import HttpErrorHandler

log = logging.getLogger(__name__)
router = APIRouter()


class ScheduledJobCreate(BaseModel):
    name: str
    method: str
    payload: dict[str, Any]
    trigger: str = "interval"
    trigger_args: dict[str, Any] = {}
    next_run_at: datetime


@router.get("/schedule/")
@HttpErrorHandler()
async def list_scheduled_jobs(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(ScheduledJobRecord))
    jobs = result.scalars().all()
    return {
        "status": "success",
        "data": {"task_result": {"scheduled_tasks": [jsonable_encoder(j) for j in jobs]}},
    }


@router.post("/schedule/", status_code=201)
@HttpErrorHandler()
async def create_scheduled_job(
    body: ScheduledJobCreate,
    session: AsyncSession = Depends(get_db_session),
):
    job = ScheduledJobRecord(
        job_id=uuid.uuid4(),
        name=body.name,
        method=body.method,
        payload=body.payload,
        trigger=body.trigger,
        trigger_args=body.trigger_args,
        next_run_at=body.next_run_at,
        enabled=True,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return {"status": "success", "data": jsonable_encoder(job)}


@router.patch("/schedule/{job_id}", status_code=200)
@HttpErrorHandler()
async def update_scheduled_job(
    job_id: str,
    body: dict[str, Any],
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(ScheduledJobRecord).where(ScheduledJobRecord.job_id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail=f"scheduled job {job_id} not found")
    for key, value in body.items():
        if hasattr(job, key):
            setattr(job, key, value)
    await session.commit()
    return {"status": "success", "data": jsonable_encoder(job)}


@router.delete("/schedule/{job_id}", status_code=204)
@HttpErrorHandler()
async def delete_scheduled_job(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(ScheduledJobRecord).where(ScheduledJobRecord.job_id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail=f"scheduled job {job_id} not found")
    await session.delete(job)
    await session.commit()

"""
Task response models — Pydantic v2.
Legacy Response/ServiceResponse shapes kept for backward compat with existing routes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class TaskResponseEnum(str, Enum):
    success = "success"
    error = "error"


class TaskStatusEnum(str, Enum):
    pending = "pending"
    queued = "queued"
    started = "started"
    finished = "finished"
    failed = "failed"
    deferred = "deferred"
    scheduled = "scheduled"


class TaskMetaData(BaseModel):
    enqueued_at: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    enqueued_elapsed_seconds: str | None = None
    total_elapsed_seconds: str | None = None
    assigned_worker: str | None = None


class TaskError(BaseModel):
    exception_class: str
    exception_args: list[str]


TaskErrorList = list[str | TaskError]


class ServiceTaskHostError(BaseModel):
    task_id: str
    task_errors: TaskErrorList


ServiceTaskErrors = list[dict[str, ServiceTaskHostError]]


class TaskResult(BaseModel):
    task_id: str
    created_on: str | None = None
    task_queue: str | None = None
    task_meta: TaskMetaData | None = None
    task_status: str
    task_result: Any = None
    task_errors: TaskErrorList | ServiceTaskErrors = []


class Response(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {
                    "task_id": "b380cf2b-ba78-4aab-b157-9b87ebbe6bb3",
                    "task_status": "pending",
                    "task_result": None,
                    "task_errors": [],
                },
            }
        }
    )

    status: TaskResponseEnum
    data: dict[str, Any]


class ResponseBasic(BaseModel):
    status: TaskResponseEnum
    data: dict[str, Any]


class ServiceResponse(BaseModel):
    status: TaskResponseEnum
    data: dict[str, Any]


# Kept for backward compat — routes still import these names
TaskResponse = TaskResult
ServiceTaskResponse = TaskResult


class WorkerResponse(BaseModel):
    hostname: Any | None = None
    pid: str | None = None
    name: Any | None = None
    last_heartbeat: Any | None = None
    birth_date: Any | None = None
    successful_job_count: Any | None = None
    failed_job_count: Any | None = None
    total_working_time: Any | None = None

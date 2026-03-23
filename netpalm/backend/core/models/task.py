"""
Task response models — Pydantic v2.
Legacy Response/ServiceResponse shapes kept for backward compat with existing routes.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

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
    enqueued_at: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    enqueued_elapsed_seconds: Optional[str] = None
    total_elapsed_seconds: Optional[str] = None
    assigned_worker: Optional[str] = None


class TaskError(BaseModel):
    exception_class: str
    exception_args: list[str]


TaskErrorList = list[Union[str, TaskError]]


class ServiceTaskHostError(BaseModel):
    task_id: str
    task_errors: TaskErrorList


ServiceTaskErrors = list[dict[str, ServiceTaskHostError]]


class TaskResult(BaseModel):
    task_id: str
    created_on: Optional[str] = None
    task_queue: Optional[str] = None
    task_meta: Optional[TaskMetaData] = None
    task_status: str
    task_result: Any = None
    task_errors: Union[TaskErrorList, ServiceTaskErrors] = []


class Response(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "task_id": "b380cf2b-ba78-4aab-b157-9b87ebbe6bb3",
                        "task_status": "pending",
                        "task_result": None,
                        "task_errors": [],
                    },
                }
            ]
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
    hostname: Optional[Any] = None
    pid: Optional[str] = None
    name: Optional[Any] = None
    last_heartbeat: Optional[Any] = None
    birth_date: Optional[Any] = None
    successful_job_count: Optional[Any] = None
    failed_job_count: Optional[Any] = None
    total_working_time: Optional[Any] = None

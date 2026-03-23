from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict


class TaskResponseEnum(str, Enum):
    success = "success"
    error = "error"


class TaskStatusEnum(str, Enum):
    queued = "queued"
    finished = "finished"
    failed = "failed"
    started = "started"
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


class TaskResponse(BaseModel):
    task_id: str
    created_on: str
    task_queue: str
    task_meta: Optional[TaskMetaData] = None
    task_status: TaskStatusEnum
    task_result: Any
    task_errors: Union[TaskErrorList, ServiceTaskErrors]


class Response(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "task_id": "b380cf2b-ba78-4aab-b157-9b87ebbe6bb3",
                        "created_on": "2020-08-02 11:16:43.693850",
                        "task_queue": "10.0.2.33",
                        "task_meta": {
                            "enqueued_at": "2020-08-02 11:16:43.693939",
                            "started_at": "2020-08-02 11:17:32.503873",
                            "ended_at": "2020-08-02 11:17:42.440347",
                            "enqueued_elapsed_seconds": "35",
                            "total_elapsed_seconds": "58",
                        },
                        "task_status": "finished",
                        "task_result": {"show run | i hostname": ["hostname cat"]},
                        "task_errors": [],
                    },
                }
            ]
        }
    )

    status: TaskResponseEnum
    data: TaskResponse


class ServiceTaskResponse(BaseModel):
    service_id: str
    task_id: str
    created_on: str
    task_queue: str
    task_meta: Optional[TaskMetaData] = None
    task_status: TaskStatusEnum
    task_result: Any
    task_errors: list[Any]


class ServiceResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "success",
                    "data": {
                        "task_id": "b380cf2b-ba78-4aab-b157-9b87ebbe6bb3",
                        "created_on": "2020-08-02 11:16:43.693850",
                        "task_queue": "10.0.2.33",
                        "task_meta": {
                            "enqueued_at": "2020-08-02 11:16:43.693939",
                            "started_at": "2020-08-02 11:17:32.503873",
                            "ended_at": "2020-08-02 11:17:42.440347",
                            "enqueued_elapsed_seconds": "35",
                            "total_elapsed_seconds": "58",
                        },
                        "task_status": "finished",
                        "task_result": {"show run | i hostname": ["hostname cat"]},
                        "task_errors": [],
                    },
                }
            ]
        }
    )

    status: TaskResponseEnum
    data: ServiceTaskResponse


class ResponseBasic(BaseModel):
    status: TaskResponseEnum
    data: dict[str, Any]


class WorkerResponse(BaseModel):
    hostname: Optional[Any] = None
    pid: str
    name: Optional[Any] = None
    last_heartbeat: Optional[Any] = None
    birth_date: Optional[Any] = None
    successful_job_count: Optional[Any] = None
    failed_job_count: Optional[Any] = None
    total_working_time: Optional[Any] = None

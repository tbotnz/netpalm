from enum import Enum
from typing import Optional, Any, List, Union, Dict

from pydantic import BaseModel


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
    enqueued_at: Optional[str]
    started_at: Optional[str]
    ended_at: Optional[str]
    enqueued_elapsed_seconds: Optional[str]
    total_elapsed_seconds: Optional[str]
    assigned_worker: Optional[str]

class TaskError(BaseModel):
    exception_class: str
    exception_args: List[str]


TaskErrorList = List[Union[str, TaskError]]

class ServiceTaskHostError(BaseModel):
    task_id: str
    task_errors: TaskErrorList


ServiceTaskErrors = List[Dict[str, ServiceTaskHostError]]


class TaskResponse(BaseModel):
    task_id: str
    created_on: str
    task_queue: str
    task_meta: Optional[TaskMetaData] = None
    task_status: TaskStatusEnum
    task_result: Any
    task_errors: Union[TaskErrorList, ServiceTaskErrors]  # Needed to get service tasks to validate when they're polled from /task/:taskid


class Response(BaseModel):
    status: TaskResponseEnum
    data: TaskResponse

    class Config:
        schema_extra = {
            "example": {
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
                        "started_elapsed_seconds": None,
                        "total_elapsed_seconds": "58"
                    },
                    "task_status": "finished",
                    "task_result": {
                        "show run | i hostname": [
                            "hostname cat"
                        ]
                    },
                    "task_errors": []
                }
            }
        }


class ServiceTaskResponse(BaseModel):
    service_id: str
    task_id: str
    created_on: str
    task_queue: str
    task_meta: Optional[TaskMetaData] = None
    task_status: TaskStatusEnum
    task_result: Any
    task_errors: list


class ServiceResponse(BaseModel):
    status: TaskResponseEnum
    data: ServiceTaskResponse

    class Config:
        schema_extra = {
            "example": {
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
                        "started_elapsed_seconds": None,
                        "total_elapsed_seconds": "58"
                    },
                    "task_status": "finished",
                    "task_result": {
                        "show run | i hostname": [
                            "hostname cat"
                        ]
                    },
                    "task_errors": []
                }
            }
        }


class ResponseBasic(BaseModel):
    status: TaskResponseEnum
    data: dict


class WorkerResponse(BaseModel):
    hostname: Optional[Any] = None
    pid: str
    name: Optional[Any] = None
    last_heartbeat: Optional[Any] = None
    birth_date: Optional[Any] = None
    successful_job_count: Optional[Any] = None
    failed_job_count: Optional[Any] = None
    total_working_time: Optional[Any] = None
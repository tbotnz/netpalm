
from typing import Optional, Set, Any, Dict
from enum import Enum, IntEnum

from pydantic import BaseModel

class task_response(str, Enum):
    success="success"
    error="error"

class task_status(str, Enum):
    queued="queued"
    finished="finished"
    failed="failed"
    started="started"
    deferred="deferred"
    scheduled="scheduled"

class model_task_meta(BaseModel):
    result: str
    errors: list

class model_task_meta_data(BaseModel):
    enqueued_at: Optional[str]
    started_at: Optional[str]
    ended_at: Optional[str]
    enqueued_elapsed_seconds: Optional[str]
    total_elapsed_seconds: Optional[str]

class model_task_response(BaseModel):
    task_id: str
    created_on: str
    task_queue: str
    task_meta: Optional[model_task_meta_data] = None
    task_status: task_status
    task_result: Any
    task_errors: list

class model_response(BaseModel):
    status: task_response
    data: model_task_response

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

class model_response_basic(BaseModel):
    status: task_response
    data: dict

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

class model_task_response(BaseModel):
    task_id: str
    created_on: str
    task_queue: str
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
                    "task_id": "6bfb7753-966f-4a1d-9894-3d93450ad4d9",
                    "created_on": "07/18/2020, 23:41:16",
                    "task_queue": "10.0.2.24",
                    "task_status": "queued",
                    "task_errors": [],
                    "task_result": ""
                }
            }
        }

class model_response_basic(BaseModel):
    status: task_response
    data: dict
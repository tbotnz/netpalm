
from typing import Optional, Set, Any, Dict
from pydantic import BaseModel

class model_task_meta(BaseModel):
    result: str
    errors: list

class model_task_response(BaseModel):
    task_id: str
    created_on: str
    task_queue: str
    task_status: str
    task_result: Any
    task_errors: list

class model_response(BaseModel):
    status: str
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
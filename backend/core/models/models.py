from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

class model_j2config(BaseModel):
    template: str
    args: dict

class model_setconfig_args(BaseModel):
    payload: Optional[Any] = None
    target: Optional[str] = None
    config: Optional[str] = None
    uri: Optional[str] = None
    action: Optional[str] = None
    
class model_setconfig(BaseModel):
    library: str
    connection_args: dict
    config: Optional[Any] = None
    j2config: Optional[model_j2config] = None
    args: Optional[model_setconfig_args] = None
    queue_strategy: Optional[str] = None

class model_script(BaseModel):
    script: str
    args: dict
    queue_strategy: Optional[str] = None

class model_getconfig(BaseModel):
    library: str
    connection_args: dict
    command: Any
    args: Optional[dict] = None
    queue_strategy: Optional[str] = None

class model_template_add(BaseModel):
    key: str
    driver: str
    command: str

class model_template_remove(BaseModel):
    template: str

class model_service(BaseModel):
    operation: str
    args: dict
    queue_strategy: Optional[str]

class model_task_response(BaseModel):
    task_id: str
    created_on: str
    task_queue: str
    task_status: str
    task_result: Any

class model_response(BaseModel):
    status: str
    data: model_task_response

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "task_id": "ff9baaf5-ca92-416a-b601-38edb801fe4f",
                    "created_on": "2020-07-02T13:11:06.090292",
                    "task_queue": "10.0.2.33",
                    "task_status": "queued",
                    "task_result": ""
                }
            }
        }

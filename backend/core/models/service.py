from typing import Optional, Set, Any, Dict, List
import typing
from pydantic import BaseModel
from enum import Enum

from backend.core.models.models import queue_strat

class service_lifecycle(str, Enum):
    create = "create"
    retrieve = "retrieve"
    delete = "delete"
    script = "script"

class model_service(BaseModel):
    operation: service_lifecycle
    args: dict
    queue_strategy: Optional[queue_strat] = None

    class Config:
        schema_extra = {
            "example": {
            "operation": "retrieve",
            "args": {
                "hosts": [
                    "10.0.2.25",
                    "10.0.2.23"
                ],
                "username": "device_username",
                "password": "device_password"
            },
            "queue_strategy": "fifo"
        }
        }

class model_service_template_methods(BaseModel):
    operation: service_lifecycle
    payload: dict

class model_service_template_methods(BaseModel):
    supported_methods: List[model_service_template_methods] = None

class model_service_template(BaseModel):
    __root__: List[model_service_template_methods]
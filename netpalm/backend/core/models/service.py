from enum import Enum
from typing import Optional, List

from pydantic import BaseModel

from netpalm.backend.core.models.models import QueueStrategy


class service_lifecycle(str, Enum):
    create = "create"
    retrieve = "retrieve"
    delete = "delete"
    validate = "validate"
    script = "script"


class model_service(BaseModel):
    operation: service_lifecycle
    args: dict
    queue_strategy: Optional[QueueStrategy] = None

    class Config:
        schema_extra = {
            "example": {
                "operation": "retrieve",
                "args": {
                    "your_payload_goes": "here"
                },
                "queue_strategy": "fifo"
            }
        }


class model_service_template_methods(BaseModel):
    operation: service_lifecycle
    path: Optional[str] = None
    payload: dict


class model_service_template_methods(BaseModel):
    supported_methods: List[model_service_template_methods] = None


class model_service_template(BaseModel):
    __root__: List[model_service_template_methods]

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel

from netpalm.backend.core.models.models import QueueStrategy


class ServiceLifecycle(str, Enum):
    create = "create"
    retrieve = "retrieve"
    delete = "delete"
    validate = "validate"
    script = "script"


class ServiceModel(BaseModel):
    operation: ServiceLifecycle
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


class ServiceModelMethods(BaseModel):
    operation: ServiceLifecycle
    path: Optional[str] = None
    payload: dict


class ServiceModelSupportedMethods(BaseModel):
    supported_methods: List[ServiceModelMethods] = None


class ServiceModelTemplate(BaseModel):
    __root__: List[ServiceModelSupportedMethods]


class ServiceInventorySchema(BaseModel):
    service_model: str
    service_id: str


class ServiceInventoryResponse(BaseModel):
    __root__: List[ServiceInventorySchema]
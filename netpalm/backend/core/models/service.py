from enum import Enum
from typing import Optional, List, Any

from pydantic import BaseModel

from netpalm.backend.core.models.models import QueueStrategy


# now redundant
class ServiceLifecycle(str, Enum):
    create = "create"
    retrieve = "retrieve"
    delete = "delete"
    validate = "validate"
    script = "script"


class ServiceInstanceState(str, Enum):
    deployed = "deployed"
    errored = "errored"
    deploying = "deploying"


class ServiceMeta(BaseModel):
    service_model: str
    created_at: str
    updated_at: Optional[str] = None
    service_id: str
    service_state: Optional[ServiceInstanceState] = None


class ServiceInstanceData(BaseModel):
    service_meta: ServiceMeta
    service_data: Any


# now redundant
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

# now redundant
class ServiceModelMethods(BaseModel):
    operation: ServiceLifecycle
    path: Optional[str] = None
    payload: dict

# now redundant
class ServiceModelSupportedMethods(BaseModel):
    supported_methods: List[ServiceModelMethods] = None

# now redundant
class ServiceModelTemplate(BaseModel):
    __root__: List[ServiceModelSupportedMethods]


class ServiceInventorySchema(BaseModel):
    service_meta: dict


class ServiceInventoryResponse(BaseModel):
    __root__: List[ServiceInventorySchema]
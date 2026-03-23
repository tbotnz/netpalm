"""
Service instance models — Pydantic v2.
ServiceInstanceState now includes all states from the new state machine.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, RootModel

from netpalm.backend.core.models.models import QueueStrategy


class ServiceLifecycle(str, Enum):
    create = "create"
    retrieve = "retrieve"
    delete = "delete"
    validate = "validate"
    script = "script"


class ServiceInstanceState(str, Enum):
    deploying = "deploying"
    deployed = "deployed"
    updating = "updating"
    deleting = "deleting"
    deleted = "deleted"
    errored = "errored"


class ServiceMeta(BaseModel):
    service_model: str
    created_at: str
    updated_at: Optional[str] = None
    service_id: str
    service_state: Optional[ServiceInstanceState] = None


class ServiceInstanceData(BaseModel):
    service_meta: ServiceMeta
    service_data: Any


class ServiceModel(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "operation": "retrieve",
                    "args": {"your_payload_goes": "here"},
                    "queue_strategy": "fifo",
                }
            ]
        }
    )

    operation: ServiceLifecycle
    args: dict[str, Any]
    queue_strategy: Optional[QueueStrategy] = None


class ServiceModelMethods(BaseModel):
    operation: ServiceLifecycle
    path: Optional[str] = None
    payload: dict[str, Any]


class ServiceModelSupportedMethods(BaseModel):
    supported_methods: Optional[list[ServiceModelMethods]] = None


class ServiceModelTemplate(RootModel[list[ServiceModelSupportedMethods]]):
    pass


class ServiceInventorySchema(BaseModel):
    service_meta: dict[str, Any]


class ServiceInventoryResponse(RootModel[list[ServiceInventorySchema]]):
    pass

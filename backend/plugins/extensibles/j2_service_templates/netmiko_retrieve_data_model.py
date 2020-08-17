from pydantic import BaseModel
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from backend.core.models.service import service_lifecycle
from backend.core.models.models import QueueStrategy

class netmiko_retrieve_data_model_args(BaseModel):
    hosts: list
    username: str
    password: str
    driver: str
    command: str

class netmiko_retrieve_data_model(BaseModel):
    operation: service_lifecycle
    args: netmiko_retrieve_data_model_args
    queue_strategy: Optional[QueueStrategy] = None

    class Config:
        schema_extra = {
            "example": {
                "operation": "retrieve",
                "args":{
                    "hosts": ["10.0.2.25","10.0.2.23"],
                    "username": "{{password}}",
                    "password": "{{username}}",
                    "driver":   "{{driver}}",
                    "command":  "{{command}}",
                }
            }
        }

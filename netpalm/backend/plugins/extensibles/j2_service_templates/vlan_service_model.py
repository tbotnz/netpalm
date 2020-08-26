from typing import Optional

from pydantic import BaseModel

from netpalm.backend.core.models.models import QueueStrategy
from netpalm.backend.core.models.service import service_lifecycle


class vlan_service_model_args(BaseModel):
    # your model goes here!
    hosts: list
    username: str
    password: str

class vlan_service_model(BaseModel):
    # this class MUST match the filename & the filename must be formatted $servicetemplatename_model.py
    operation: service_lifecycle
    args: vlan_service_model_args
    queue_strategy: Optional[QueueStrategy] = None

    class Config:
        # add an example payload under the "example" dict 
        schema_extra = {
            "example": {
                "operation": "create",
                "args":{
                    "hosts":["10.0.2.25","10.0.2.23"],
                    "username":"admin",
                    "password":"admin"
                }
            }
        }
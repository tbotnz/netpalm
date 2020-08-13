from pydantic import BaseModel
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple, Union

from backend.core.models.service import service_lifecycle
from backend.core.models.models import queue_strat

class snmp_service_model_args(BaseModel):
    # your model goes here!
    hosts: list
    username: str
    password: str
    snmp_community: str
    snmp_location: str
    snmp_contact: str

class snmp_service_model(BaseModel):
    # this class MUST match the filename & the filename must be formatted $servicetemplatename_model.py
    operation: service_lifecycle
    args: snmp_service_model_args
    queue_strategy: Optional[queue_strat] = None

    class Config:
        # add an example payload under the "example" dict 
        schema_extra = {
            "example": {
                "operation": "create",
                "args":{
                    "hosts":["10.0.2.25","10.0.2.23"],
                }
            }
        }
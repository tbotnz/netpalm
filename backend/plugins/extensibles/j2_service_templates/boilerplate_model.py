from typing import Optional

from pydantic import BaseModel

from backend.core.models.models import QueueStrategy
from backend.core.models.service import service_lifecycle


class boilerplate_model_args(BaseModel):
    # your model goes here!
    hosts: list

class boilerplate_model(BaseModel):
    # this class MUST match the filename & the filename must be formatted $servicetemplatename_model.py
    operation: service_lifecycle
    args: boilerplate_model_args
    queue_strategy: Optional[QueueStrategy] = None

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
from typing import Optional

from pydantic import BaseModel

from backend.core.models.models import QueueStrategy
from backend.core.models.models import Webhook

class hello_world_model_args(BaseModel):
    # your model goes here!
    hello: str

class hello_world_model(BaseModel):
    # this class MUST match the filename & the filename must be formatted $servicetemplatename_model.py
    script: str
    args: hello_world_model_args
    queue_strategy: Optional[QueueStrategy] = None
    webhook: Optional[Webhook] = None

    class Config:
        # add an example payload under the "example" dict 
        schema_extra = {
            "example": {
                "script": "hello_world",
                "args": {
                    "hello": "world"
                },
                "queue_strategy": "fifo"
            }
        }

from typing import Optional

from pydantic import BaseModel

from backend.core.models.models import QueueStrategy
from backend.core.models.service import service_lifecycle


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
    queue_strategy: Optional[QueueStrategy] = None

    class Config:
        # add an example payload under the "example" dict 
        schema_extra = {
            "example": {
                "operation": "retrieve",
                "args": {
                    "hosts": [
                        "10.0.2.25",
                        "10.0.2.23",
                        "10.0.2.21"
                    ],
                    "username": "{{device_username}}",
                    "password": "{{device_password}}",
                    "snmp_community": "test_community",
                    "snmp_location": "test_location",
                    "snmp_contact": "test_contact"

                },
                "queue_strategy": "fifo"
            }
        }

from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

from backend.core.models.models import model_j2config

class model_restconf_connection_args(BaseModel):
    host: str
    username: str
    password: str
    port: int
    verify: bool
    transport: str
    headers: dict

class model_restconf_payload(BaseModel):
    uri: str
    action: str
    payload: Optional[dict]

class model_restconf(BaseModel):
    library: str
    connection_args: model_restconf_connection_args
    args: model_restconf_payload
    queue_strategy: Optional[str] = "fifo"

    class Config:
        schema_extra = {
            "example": {
                    "library": "restconf",
                    "connection_args":{
                        "host":"ios-xe-mgmt-latest.cisco.com", "port":9443, "username":"developer", "password":"C1sco12345", "verify":False, "timeout":10, "transport":"https", "headers":{
                            "Content-Type": "application/yang-data+json", "Accept": "application/yang-data+json"
                        }
                    },
                    "args":{
                        "uri":"/restconf/data/Cisco-IOS-XE-native:native/interface/",
                    "action":"post",
                    "payload": {
                        "Cisco-IOS-XE-native:BDI":{
                        "name":"4001",
                        "description": "netpalm"
                        }
                    }
                    },
                    "queue_strategy": "fifo"
            }
        }
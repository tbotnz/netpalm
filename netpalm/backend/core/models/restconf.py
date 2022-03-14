from enum import Enum
from typing import Optional

from pydantic import BaseModel

from netpalm.backend.core.models.models import CacheConfig
from netpalm.backend.core.models.models import QueueStrategy
from netpalm.backend.core.models.models import Webhook


class SupportedOptions(str, Enum):
    get = "get"
    post = "post"
    patch = "patch"
    put = "put"
    delete = "delete"


class RestconfConnectionArgs(BaseModel):
    host: str
    username: str
    password: str
    port: int
    verify: bool
    transport: str
    headers: dict


class RestconfPayload(BaseModel):
    uri: str
    action: SupportedOptions
    payload: Optional[dict] = None


class Restconf(BaseModel):
    connection_args: RestconfConnectionArgs
    args: RestconfPayload
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = {}
    ttl: Optional[int] = None

    class Config:
        schema_extra = {
            "example": {
                "library": "restconf",
                "connection_args": {
                    "host": "ios-xe-mgmt-latest.cisco.com", "port": 9443, "username": "developer",
                    "password": "C1sco12345", "verify": False, "timeout": 10, "transport": "https", "headers": {
                        "Content-Type": "application/yang-data+json", "Accept": "application/yang-data+json"
                    }
                },
                "args": {
                    "uri": "/restconf/data/Cisco-IOS-XE-native:native/interface/",
                    "action": "post",
                    "payload": {
                        "Cisco-IOS-XE-native:BDI": {
                            "name": "4001",
                            "description": "netpalm"
                        }
                    }
                },
                "queue_strategy": "fifo",
                "cache": {
                    "enabled": True,
                    "ttl": 300,
                    "poison": False
                }
            }
        }

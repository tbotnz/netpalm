
from enum import Enum
from typing import Optional, Any, List, Union

from pydantic import BaseModel

from netpalm.backend.core.models.napalm import NapalmGetConfig
from netpalm.backend.core.models.ncclient import NcclientGetConfig
from netpalm.backend.core.models.netmiko import NetmikoGetConfig
from netpalm.backend.core.models.restconf import Restconf


class GetConfig(BaseModel):
    __root__: Union[NapalmGetConfig, NcclientGetConfig, NetmikoGetConfig, Restconf]

    class Config:
        schema_extra = {
            "example": {
                "library": "netmiko",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "device_username",
                    "password": "device_password"
                },
                "command": "show ip int brief",
                "args": {
                    "use_textfsm": True
                },
                "queue_strategy": "pinned",
                "cache": {
                    "enabled": True,
                    "ttl": 300,
                    "poison": False
                }
            }
        }

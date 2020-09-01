
from enum import Enum
from typing import Optional, Any, List, Union

from pydantic import BaseModel

from netpalm.backend.core.models.napalm import NapalmSetConfig
from netpalm.backend.core.models.ncclient import NcclientSetConfig
from netpalm.backend.core.models.netmiko import NetmikoSetConfig
from netpalm.backend.core.models.restconf import Restconf


class SetConfig(BaseModel):
    __root__:Union[NapalmSetConfig, NcclientSetConfig, NetmikoSetConfig, Restconf]

    class Config:
        schema_extra = {
            "example": {
                "library": "napalm",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "device_username",
                    "password": "device_password"
                },
                "j2config": {
                    "template": "test",
                    "args": {
                        "vlans": [
                            "5",
                            "3",
                            "2"
                        ]
                    }
                },
                "queue_strategy": "fifo",
                "pre_checks": [
                    {
                        "match_type": "include",
                        "get_config_args": {
                            "command": "show run | i hostname"
                        },
                        "match_str": [
                            "hostname cat"
                        ]
                    }
                ],
                "post_checks": [
                    {
                        "match_type": "include",
                        "get_config_args": {
                            "command": "show run | i hostname"
                        },
                        "match_str": [
                            "hostname dog"
                        ]
                    }
                ]
            }
        }

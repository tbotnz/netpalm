from typing import Optional, Any, List

from pydantic import BaseModel

from backend.core.models.base_models import Webhook, J2Config, CacheConfig, GenericPrePostCheck, LibraryName, \
    QueueStrategy


class SetConfigArgs(BaseModel):
    payload: Optional[Any] = None
    target: Optional[str] = None
    config: Optional[str] = None
    uri: Optional[str] = None
    action: Optional[str] = None


class SetConfig(BaseModel):
    library: LibraryName
    connection_args: dict
    config: Optional[Any] = None
    j2config: Optional[J2Config] = None
    args: Optional[SetConfigArgs] = {}
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    pre_checks: Optional[List[GenericPrePostCheck]] = None
    post_checks: Optional[List[GenericPrePostCheck]] = None

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


class Script(BaseModel):
    script: str
    args: Optional[dict] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None

    class Config:
        schema_extra = {
            "example": {
                "script": "hello_world",
                "args": {
                    "hello": "world"
                },
                "queue_strategy": "fifo"
            }
        }


class GetConfig(BaseModel):
    library: LibraryName
    connection_args: dict
    command: Any
    args: Optional[dict] = {}
    webhook: Optional[Webhook] = {}
    queue_strategy: Optional[QueueStrategy] = None
    post_checks: Optional[List[GenericPrePostCheck]] = []
    cache: Optional[CacheConfig] = {}

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

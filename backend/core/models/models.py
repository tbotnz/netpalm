from typing import Optional, Set, Any, Dict, List
import typing
from pydantic import BaseModel
from enum import Enum, IntEnum

class queue_strat(str, Enum):
    fifo = "fifo"
    pinned = "pinned"

class lib_opts_all(str, Enum):
    napalm = "napalm"
    ncclient = "ncclient"
    restconf = "restconf"
    netmiko = "netmiko"

class check_enum(str, Enum):
    include = "include"
    exclude = "exclude"

class get_config_args(BaseModel):
    command: str

class model_generic_pre_post_check(BaseModel):
    match_type: check_enum
    match_str: list
    get_config_args: get_config_args

class model_webhook(BaseModel):
    name: Optional[str] = None
    args: Optional[dict] = None
    j2template: Optional[str] = None

class model_j2config(BaseModel):
    template: str
    args: dict

class model_setconfig_args(BaseModel):
    payload: Optional[Any] = None
    target: Optional[str] = None
    config: Optional[str] = None
    uri: Optional[str] = None
    action: Optional[str] = None

class model_setconfig(BaseModel):
    library: lib_opts_all
    connection_args: dict
    config: Optional[Any] = None
    j2config: Optional[model_j2config] = None
    args: Optional[model_setconfig_args] = None
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[queue_strat] = None
    pre_checks: Optional[List[model_generic_pre_post_check]] = None
    post_checks: Optional[List[model_generic_pre_post_check]] = None

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


class model_script(BaseModel):
    script: str
    args: Optional[dict] = None
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[queue_strat] = None

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


class model_cache_config(BaseModel):
    enabled: bool = False
    ttl: Optional[int] = None
    poison: Optional[bool] = False

    class Config:
        schema_extra = {
            'example': {
                'enabled': True,
                'ttl': 300,
                'poison': False
            }
        }


class model_getconfig(BaseModel):
    library: lib_opts_all
    connection_args: dict
    command: Any
    args: Optional[dict] = {}
    webhook: Optional[model_webhook] = {}
    queue_strategy: Optional[queue_strat] = None
    post_checks: Optional[List[model_generic_pre_post_check]] = []
    cache: Optional[model_cache_config] = {}

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


class model_template_add(BaseModel):
    key: str = None
    driver: str  = None
    command: str  = None

class model_template_remove(BaseModel):
    template: str  = None

class model_general_error(BaseModel):
    status: str  = None
    data: dict  = None

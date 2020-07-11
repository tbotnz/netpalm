from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

from backend.core.models.models import model_j2config

class netmiko_send_config_args(BaseModel):
    command_string: Optional[str] = None
    expect_string: Optional[str] = None
    delay_factor: Optional[int] = None
    max_loops: Optional[int] = None
    auto_find_prompt: Optional[bool] = None
    strip_prompt: Optional[bool] = None
    strip_command: Optional[bool] = None
    normalize: Optional[bool] = None
    use_textfsm: Optional[bool] = None
    textfsm_template: Optional[str] = None
    use_genie: Optional[bool] = None
    cmd_verify: Optional[bool] = None

class model_netmiko_getconfig(BaseModel):
    library: str
    connection_args: dict
    command: Optional[Any] = None
    args: Optional[netmiko_send_config_args] = None
    queue_strategy: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "library": "netmiko",
                "connection_args":{
                    "device_type":"cisco_ios", "host":"10.0.2.33", "username":"admin", "password":"admin"
                },
                "command": "show ip int brief",
                "args":{
                    "use_textfsm":True
                },
                "queue_strategy": "fifo"  
            }
        }

class model_netmiko_setconfig(BaseModel):
    library: str
    connection_args: dict
    config: Optional[Any] = None
    args: Optional[netmiko_send_config_args] = None
    j2config: Optional[model_j2config] = None
    queue_strategy: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
            "library": "netmiko",
            "connection_args":{
                "device_type":"cisco_ios", "host":"10.0.2.33", "username":"admin", "password":"admin"
            },
            "config": ["hostname cat"],
            "queue_strategy": "pinned"
            }
        }

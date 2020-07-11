from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

from backend.core.models.models import model_j2config

class netmiko_send_config_args(BaseModel):
    command_string: Optional[str]
    expect_string: Optional[str]
    delay_factor: Optional[int]
    max_loops: Optional[int]
    auto_find_prompt: Optional[bool]
    strip_prompt: Optional[bool]
    strip_command: Optional[bool]
    normalize: Optional[bool]
    use_textfsm: Optional[bool]
    textfsm_template: Optional[str]
    use_genie: Optional[bool]
    cmd_verify: Optional[bool]

class model_netmiko_getconfig(BaseModel):
    library: str
    connection_args: dict
    command: Optional[Any]
    args: Optional[netmiko_send_config_args]
    queue_strategy: Optional[str] = "fifo"

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
    config: Optional[Any]
    args: Optional[netmiko_send_config_args]
    j2config: Optional[model_j2config]
    queue_strategy: Optional[str] = "fifo"

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

from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

from backend.core.models.models import model_j2config

class napalm_optional_connection_args(BaseModel):
    fortios_vdom: Optional[str]
    port: Optional[int]
    config_lock: Optional[bool]
    dest_file_system: Optional[str]
    auto_rollback_on_error: Optional[bool]
    global_delay_factor: Optional[int]
    nxos_protocol: Optional[str]

class napalm_connection_args(BaseModel):
    device_type = str
    optional_args = dict
    host = str
    username = str
    password = str

class model_napalm_getconfig(BaseModel):
    library: str
    connection_args: napalm_connection_args
    command: Any
    queue_strategy: Optional[str] = "fifo"

    class Config:
        schema_extra = {
            "example": {
                "library": "napalm",
                "connection_args":{
                    "device_type":"cisco_ios", "host":"10.0.2.23", "username":"admin", "password":"admin"
                },
                "command": "get_facts",
                "queue_strategy": "fifo"
            }
        }

class model_napalm_setconfig(BaseModel):
    library: str
    connection_args: napalm_connection_args
    config: Optional[Any]
    j2config: Optional[model_j2config]
    queue_strategy: Optional[str] = "fifo"

    class Config:
        schema_extra = {
            "example": {
                "library": "napalm",
                "connection_args":{
                    "device_type":"cisco_ios", "host":"10.0.2.33", "username":"admin", "password":"admin"
                },
                "config": "hostnam cat",
                "queue_strategy": "fifo"
            }
        }
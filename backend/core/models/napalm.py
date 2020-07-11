from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

from backend.core.models.models import model_j2config

class napalm_optional_connection_args(BaseModel):
    fortios_vdom: Optional[str] = None
    port: Optional[int] = None
    config_lock: Optional[bool] = None
    dest_file_system: Optional[str] = None
    auto_rollback_on_error: Optional[bool] = None
    global_delay_factor: Optional[int] = None
    nxos_protocol: Optional[str] = None

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
    queue_strategy: Optional[str] = None

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
    config: Optional[Any] = None
    j2config: Optional[model_j2config] = None
    queue_strategy: Optional[str] = None

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
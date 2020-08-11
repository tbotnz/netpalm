from typing import Optional, Set, Any, Dict, List
from enum import Enum, IntEnum

import typing
from pydantic import BaseModel

from backend.core.models.models import model_j2config
from backend.core.models.models import model_webhook
from backend.core.models.models import model_generic_pre_post_check
from backend.core.models.models import queue_strat

class lib_opts_napalm(str, Enum):
    napalm = "napalm"

class napalm_device_type(str, Enum):
    cisco_ios = "cisco_ios"
    cisco_xr = "iosxr"
    nxos = "nxos"
    cisco_nxos_ssh = "nxos_ssh"
    arista_eos = "eos"
    juniper = "junos"
    
class napalm_optional_connection_args(BaseModel):
    fortios_vdom: Optional[str] = None
    port: Optional[int] = None
    config_lock: Optional[bool] = None
    dest_file_system: Optional[str] = None
    auto_rollback_on_error: Optional[bool] = None
    global_delay_factor: Optional[int] = None
    nxos_protocol: Optional[str] = None

class napalm_connection_args(BaseModel):
    device_type: napalm_device_type
    optional_args: Optional[napalm_optional_connection_args] = None
    host: str
    username: str
    password: str

class model_napalm_getconfig(BaseModel):
    library: lib_opts_napalm
    connection_args: napalm_connection_args
    command: Any
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[queue_strat] = None
    post_checks: Optional[List[model_generic_pre_post_check]] = None
    
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
    library: lib_opts_napalm
    connection_args: napalm_connection_args
    config: Optional[Any] = None
    j2config: Optional[model_j2config] = None
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[queue_strat] = None
    pre_checks: Optional[List[model_generic_pre_post_check]] = None
    post_checks: Optional[List[model_generic_pre_post_check]] = None

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
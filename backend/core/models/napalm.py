from enum import Enum
from typing import Optional

from pydantic import BaseModel

from backend.core.models.base_models import BaseConnectionArgs, BaseGetConfig, BaseSetConfig


class NapalmDeviceType(str, Enum):
    cisco_ios = "cisco_ios"
    cisco_xr = "iosxr"
    nxos = "nxos"
    cisco_nxos_ssh = "nxos_ssh"
    arista_eos = "eos"
    juniper = "junos"


class NapalmConnectionOptionalArgs(BaseModel):
    fortios_vdom: Optional[str] = None
    port: Optional[int] = None
    config_lock: Optional[bool] = None
    dest_file_system: Optional[str] = None
    auto_rollback_on_error: Optional[bool] = None
    global_delay_factor: Optional[int] = None
    nxos_protocol: Optional[str] = None


class NapalmConnectionArgs(BaseConnectionArgs):
    device_type: NapalmDeviceType
    optional_args: Optional[NapalmConnectionOptionalArgs] = None


class NapalmGetConfig(BaseGetConfig):
    class Config:
        schema_extra = {
            "example": {
                "library": "napalm",
                "connection_args": {
                    "device_type": "cisco_ios", "host": "10.0.2.23", "username": "admin", "password": "admin"
                },
                "command": "get_facts",
                "queue_strategy": "fifo",
                "cache": {
                    "enabled": True,
                    "ttl": 300,
                    "poison": False
                }
            }
        }


class NapalmSetConfig(BaseSetConfig):
    class Config:
        schema_extra = {
            "example": {
                "library": "napalm",
                "connection_args": {
                    "device_type": "cisco_ios", "host": "10.0.2.33", "username": "admin", "password": "admin"
                },
                "config": "hostnam cat",
                "queue_strategy": "fifo"
            }
        }

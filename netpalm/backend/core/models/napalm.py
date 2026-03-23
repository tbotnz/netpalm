from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from netpalm.backend.core.models.models import (
    CacheConfig,
    GenericPrePostCheck,
    J2Config,
    QueueStrategy,
    Webhook,
)


class NapalmDeviceType(str, Enum):
    cisco_ios = "cisco_ios"
    cisco_xr = "cisco_xr"
    nxos = "nxos"
    cisco_nxos_ssh = "cisco_nxos_ssh"
    arista_eos = "arista_eos"
    juniper = "juniper"


class NapalmConnectionOptionalArgs(BaseModel):
    fortios_vdom: Optional[str] = None
    port: Optional[int] = None
    config_lock: Optional[bool] = None
    dest_file_system: Optional[str] = None
    auto_rollback_on_error: Optional[bool] = None
    global_delay_factor: Optional[int] = None
    nxos_protocol: Optional[str] = None


class NapalmConnectionArgs(BaseModel):
    device_type: NapalmDeviceType
    optional_args: Optional[NapalmConnectionOptionalArgs] = None
    host: str
    username: str
    password: str


class NapalmGetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "library": "napalm",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.23",
                    "username": "admin",
                    "password": "admin",
                },
                "command": "get_facts",
                "queue_strategy": "fifo",
                "cache": {"enabled": True, "ttl": 300, "poison": False},
            }
        }
    )

    connection_args: NapalmConnectionArgs
    command: Any
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    post_checks: Optional[list[GenericPrePostCheck]] = None
    cache: Optional[CacheConfig] = None


class NapalmSetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "library": "napalm",
                "connection_args": {
                    "device_type": "cisco_ios",
                    "host": "10.0.2.33",
                    "username": "admin",
                    "password": "admin",
                },
                "config": "hostnam cat",
                "queue_strategy": "fifo",
            }
        }
    )

    connection_args: NapalmConnectionArgs
    config: Optional[Any] = None
    j2config: Optional[J2Config] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    pre_checks: Optional[list[GenericPrePostCheck]] = None
    post_checks: Optional[list[GenericPrePostCheck]] = None

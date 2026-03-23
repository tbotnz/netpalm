from enum import Enum
from typing import Any

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
    fortios_vdom: str | None = None
    port: int | None = None
    config_lock: bool | None = None
    dest_file_system: str | None = None
    auto_rollback_on_error: bool | None = None
    global_delay_factor: int | None = None
    nxos_protocol: str | None = None


class NapalmConnectionArgs(BaseModel):
    device_type: NapalmDeviceType
    optional_args: NapalmConnectionOptionalArgs | None = None
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
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    post_checks: list[GenericPrePostCheck] | None = None
    cache: CacheConfig | None = None


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
    config: Any | None = None
    j2config: J2Config | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    pre_checks: list[GenericPrePostCheck] | None = None
    post_checks: list[GenericPrePostCheck] | None = None

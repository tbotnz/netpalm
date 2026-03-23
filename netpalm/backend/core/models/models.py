from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class QueueStrategy(str, Enum):
    fifo = "fifo"


class LibraryName(str, Enum):
    napalm = "napalm"
    ncclient = "ncclient"
    restconf = "restconf"
    netmiko = "netmiko"
    puresnmp = "puresnmp"


class CheckEnum(str, Enum):
    include = "include"
    exclude = "exclude"


class GetConfigArgs(BaseModel):
    command: str


class GenericPrePostCheck(BaseModel):
    match_type: CheckEnum
    match_str: list[str]
    get_config_args: GetConfigArgs


class Webhook(BaseModel):
    name: Optional[str] = None
    args: Optional[dict[str, Any]] = None
    j2template: Optional[str] = None


class J2Config(BaseModel):
    template: str
    args: dict[str, Any]


class SetConfigArgs(BaseModel):
    payload: Optional[Any] = None
    default_operation: Optional[str] = None
    target: Optional[str] = None
    config: Optional[str] = None
    uri: Optional[str] = None
    action: Optional[str] = None
    render_json: bool = False


class SetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "library": "napalm",
                    "connection_args": {
                        "device_type": "cisco_ios",
                        "host": "10.0.2.33",
                        "username": "device_username",
                        "password": "device_password",
                    },
                    "j2config": {
                        "template": "test",
                        "args": {"vlans": ["5", "3", "2"]},
                    },
                    "queue_strategy": "fifo",
                    "pre_checks": [
                        {
                            "match_type": "include",
                            "get_config_args": {"command": "show run | i hostname"},
                            "match_str": ["hostname cat"],
                        }
                    ],
                    "post_checks": [
                        {
                            "match_type": "include",
                            "get_config_args": {"command": "show run | i hostname"},
                            "match_str": ["hostname dog"],
                        }
                    ],
                }
            ]
        }
    )

    library: LibraryName
    connection_args: dict[str, Any]
    config: Optional[Any] = None
    j2config: Optional[J2Config] = None
    args: Optional[SetConfigArgs] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    pre_checks: Optional[list[GenericPrePostCheck]] = None
    post_checks: Optional[list[GenericPrePostCheck]] = None
    enable_mode: bool = False


class CacheConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"enabled": True, "ttl": 300, "poison": False}]
        }
    )

    enabled: bool = False
    ttl: Optional[int] = None
    poison: bool = False


class Script(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "script": "hello_world",
                    "args": {"hello": "world"},
                    "queue_strategy": "fifo",
                }
            ]
        }
    )

    script: str
    args: Optional[dict[str, Any]] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = None


class ScriptCustom(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"script": "hello_world", "queue_strategy": "fifo"}]
        }
    )

    script: str
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = None


class GetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "library": "netmiko",
                    "connection_args": {
                        "device_type": "cisco_ios",
                        "host": "10.0.2.33",
                        "username": "device_username",
                        "password": "device_password",
                    },
                    "command": "show ip int brief",
                    "args": {"use_textfsm": True, "render_json": True},
                    "queue_strategy": "fifo",
                    "cache": {"enabled": True, "ttl": 300, "poison": False},
                }
            ]
        }
    )

    library: LibraryName
    connection_args: dict[str, Any]
    command: Any
    args: Optional[dict[str, Any]] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    post_checks: Optional[list[GenericPrePostCheck]] = None
    cache: Optional[CacheConfig] = None


class TFSMPushTemplateModel(BaseModel):
    driver: str
    command: str
    template_text: str


class TFSMTemplateAdd(BaseModel):
    key: str
    driver: str
    command: str


class TFSMTemplateRemove(BaseModel):
    template: Optional[str] = None


class TFSMTemplateMatch(BaseModel):
    driver: str
    command: str


class TFSMTemplateMatchResponse(BaseModel):
    """Data returned from TextFSM Library Index lookup"""

    Template: str
    Hostname: str
    Platform: str
    Command: str
    template_text: str


class UniversalTemplateAdd(BaseModel):
    """General template ingestor for handling base64 ingestion and writing"""

    base64_payload: str
    name: str


class UniversalTemplateRemove(BaseModel):
    """General template remover"""

    name: Optional[str] = None


class GeneralError(BaseModel):
    status: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class PinnedStore(BaseModel):
    hostname: str
    count: int
    limit: int
    pinned_listen_queue: str


class ScheduleBase(BaseModel):
    path: str
    payload: dict[str, Any]


class ScheduleInterval(BaseModel):
    weeks: Optional[int] = None
    days: Optional[int] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    seconds: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timezone: Optional[str] = None
    jitter: Optional[int] = None
    schedule_payload: ScheduleBase

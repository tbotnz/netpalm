"""
Pydantic v2 request/response models for netpalm API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class QueueStrategy(StrEnum):
    fifo = "fifo"
    pinned = "pinned"


class LibraryName(StrEnum):
    napalm = "napalm"
    ncclient = "ncclient"
    restconf = "restconf"
    netmiko = "netmiko"
    puresnmp = "puresnmp"


class CheckEnum(StrEnum):
    include = "include"
    exclude = "exclude"


class GetConfigArgs(BaseModel):
    command: str


class GenericPrePostCheck(BaseModel):
    match_type: CheckEnum
    match_str: list[str]
    get_config_args: GetConfigArgs


class Webhook(BaseModel):
    name: str | None = None
    args: dict[str, Any] | None = None
    j2template: str | None = None


class J2Config(BaseModel):
    template: str
    args: dict[str, Any]


class SetConfigArgs(BaseModel):
    payload: Any | None = None
    default_operation: str | None = None
    target: str | None = None
    config: str | None = None
    uri: str | None = None
    action: str | None = None
    render_json: bool = False


class SetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    library: LibraryName
    connection_args: dict[str, Any]
    config: Any | None = None
    j2config: J2Config | None = None
    args: SetConfigArgs | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    pre_checks: list[GenericPrePostCheck] | None = None
    post_checks: list[GenericPrePostCheck] | None = None
    enable_mode: bool = False


class CacheConfig(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"enabled": True, "ttl": 300, "poison": False}})

    enabled: bool = False
    ttl: int | None = None
    poison: bool = False


class Script(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "script": "hello_world",
                "args": {"hello": "world"},
                "queue_strategy": "fifo",
            }
        }
    )

    script: str
    args: dict[str, Any] | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    cache: CacheConfig | None = None


class ScriptCustom(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"script": "hello_world", "queue_strategy": "fifo"}})

    script: str
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    cache: CacheConfig | None = None


class GetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    library: LibraryName
    connection_args: dict[str, Any]
    command: Any
    args: dict[str, Any] | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    post_checks: list[GenericPrePostCheck] | None = None
    cache: CacheConfig | None = None


class TFSMPushTemplateModel(BaseModel):
    driver: str
    command: str
    template_text: str


class TFSMTemplateAdd(BaseModel):
    key: str
    driver: str
    command: str


class TFSMTemplateRemove(BaseModel):
    template: str | None = None


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

    name: str | None = None


class GeneralError(BaseModel):
    status: str | None = None
    data: dict[str, Any] | None = None


class PinnedStore(BaseModel):
    hostname: str
    count: int
    limit: int
    pinned_listen_queue: str


class ScheduleBase(BaseModel):
    path: str
    payload: dict[str, Any]


class ScheduleInterval(BaseModel):
    weeks: int | None = None
    days: int | None = None
    hours: int | None = None
    minutes: int | None = None
    seconds: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    timezone: str | None = None
    jitter: int | None = None
    schedule_payload: ScheduleBase


# ── Kafka payload models ──────────────────────────────────────────────────────


class TaskMessage(BaseModel):
    """Message produced to Kafka job topics by the Scheduler."""

    task_id: uuid.UUID
    method: str
    kwargs: dict[str, Any]
    queue_strategy: QueueStrategy = QueueStrategy.fifo
    pinned_host: str | None = None


class ResultMessage(BaseModel):
    """Message produced to netpalm.results by the Executor."""

    task_id: uuid.UUID
    status: str
    result: Any = None
    error: str | None = None


# ── Event model ───────────────────────────────────────────────────────────────


class NetpalmEvent(BaseModel):
    """Parsed event produced by an EventListener."""

    source_topic: str
    device_host: str | None = None
    event_type: str
    raw: bytes
    data: dict[str, Any] = {}


# ── API response models ───────────────────────────────────────────────────────


class TaskResponse(BaseModel):
    """Returned by QueueBroker and task result endpoints."""

    task_id: uuid.UUID
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class ServiceTaskResponse(BaseModel):
    """Returned by service creation/update/delete endpoints."""

    service_id: uuid.UUID
    task_id: uuid.UUID
    status: str


class ServiceInstanceData(BaseModel):
    """Current state of a service instance."""

    service_id: uuid.UUID
    service_model: str
    state: str
    data: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    current_version: int


class ServiceVersionSummary(BaseModel):
    """Summary of a service instance version snapshot."""

    version_id: uuid.UUID
    service_id: uuid.UUID
    version: int
    state: str
    created_at: datetime

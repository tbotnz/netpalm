from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

from netpalm.backend.core.models.models import CacheConfig, QueueStrategy, Webhook


class PureSNMPConnectionArgs(BaseModel):
    host: str
    community: str
    port: int | None = None
    timeout: int | None = None


class SNMPtypes(StrEnum):
    table = "table"
    get = "get"
    walk = "walk"


class PureSNMPArgs(BaseModel):
    type: SNMPtypes


class PureSNMPGetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "library": "puresnmp",
                "connection_args": {
                    "host": "10.0.2.33",
                    "community": "test",
                    "port": 161,
                    "timeout": 2,
                },
                "command": [
                    ".1.3.6.1.4.1.9.2.1.58.0",
                    "1.3.6.1.2.1.1.2.0",
                    "1.3.6.1.2.1.1.3.0",
                ],
                "queue_strategy": "fifo",
            }
        }
    )

    connection_args: PureSNMPConnectionArgs
    command: Any
    args: PureSNMPArgs
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    cache: CacheConfig | None = None

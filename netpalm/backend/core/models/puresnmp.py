from typing import Optional, Any

from pydantic import BaseModel

from netpalm.backend.core.models.models import CacheConfig
from netpalm.backend.core.models.models import QueueStrategy
from netpalm.backend.core.models.models import Webhook


class PureSNMPConnectionArgs(BaseModel):
    host: str
    community: str
    port: Optional[int] = None
    timeout: Optional[int] = None


class PureSNMPGetConfig(BaseModel):
    connection_args: PureSNMPConnectionArgs
    command: Any
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = {}

    class Config:
        schema_extra = {
            "example": {
                "library": "puresnmp",
                "connection_args": {
                    "host": "10.0.2.33",
                    "community": "test",
                    "port": 161,
                    "timeout": 2
                },
                "command": [".1.3.6.1.4.1.9.2.1.58.0","1.3.6.1.2.1.1.2.0", "1.3.6.1.2.1.1.3.0"],
                "queue_strategy": "fifo"
            }
        }

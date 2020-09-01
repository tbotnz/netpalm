from enum import Enum
from typing import Optional, Any, List, Union

from pydantic import BaseModel


class QueueStrategy(str, Enum):
    fifo = "fifo"
    pinned = "pinned"


class LibraryName(str, Enum):
    napalm = "napalm"
    ncclient = "ncclient"
    restconf = "restconf"
    netmiko = "netmiko"


class CheckEnum(str, Enum):
    include = "include"
    exclude = "exclude"


class GetConfigArgs(BaseModel):
    command: str


class GenericPrePostCheck(BaseModel):
    match_type: CheckEnum
    match_str: list
    get_config_args: GetConfigArgs


class Webhook(BaseModel):
    name: Optional[str] = None
    args: Optional[dict] = None
    j2template: Optional[str] = None


class J2Config(BaseModel):
    template: str
    args: dict


class SetConfigArgs(BaseModel):
    payload: Optional[Any] = None
    target: Optional[str] = None
    config: Optional[str] = None
    uri: Optional[str] = None
    action: Optional[str] = None


class Script(BaseModel):
    script: str
    args: Optional[dict] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None

    class Config:
        schema_extra = {
            "example": {
                "script": "hello_world",
                "args": {
                    "hello": "world"
                },
                "queue_strategy": "fifo"
            }
        }


class CacheConfig(BaseModel):
    enabled: bool = False
    ttl: Optional[int] = None
    poison: Optional[bool] = False

    class Config:
        schema_extra = {
            'example': {
                'enabled': True,
                'ttl': 300,
                'poison': False
            }
        }


class TFSMPushTemplateModel(BaseModel):
    driver: str
    command: str
    template_text: str


class TemplateAdd(BaseModel):
    key: str
    driver: str
    command: str


class TemplateRemove(BaseModel):
    template: str = None


class GeneralError(BaseModel):
    status: str = None
    data: dict = None

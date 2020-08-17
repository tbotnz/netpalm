from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TemplateAdd(BaseModel):
    key: str = None
    driver: str = None
    command: str = None


class TemplateRemove(BaseModel):
    template: str = None


class GeneralError(BaseModel):
    status: str = None
    data: dict = None


class Webhook(BaseModel):
    name: Optional[str] = None
    args: Optional[dict] = None
    j2template: Optional[str] = None


class J2Config(BaseModel):
    template: str
    args: dict


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


class LibraryName(str, Enum):
    napalm = "napalm"
    ncclient = "ncclient"
    restconf = "restconf"
    netmiko = "netmiko"


class CheckEnum(str, Enum):
    include = "include"
    exclude = "exclude"


class QueueStrategy(str, Enum):
    fifo = "fifo"
    pinned = "pinned"


class GetConfigArgs(BaseModel):
    command: str


class GenericPrePostCheck(BaseModel):
    match_type: CheckEnum
    match_str: list
    get_config_args: GetConfigArgs


class BaseConnectionArgs(BaseModel):
    host: str
    username: str
    password: str
    port: Optional[int]

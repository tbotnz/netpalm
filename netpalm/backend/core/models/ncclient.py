from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict

from netpalm.backend.core.models.models import (
    CacheConfig,
    J2Config,
    QueueStrategy,
    Webhook,
)


class NcclientSendConfigArgs(BaseModel):
    target: Optional[str] = None
    config: Optional[str] = None
    default_operation: Optional[str] = None
    render_json: bool = False


class NcclientGetConfigArgs(BaseModel):
    source: str
    filter: Optional[str] = None
    render_json: bool = False
    capabilities: bool = False


class NcclientGetRpcArgs(BaseModel):
    rpc: str
    render_json: bool = False
    capabilities: bool = False


class NcclientDeviceDrivers(str, Enum):
    default = "default"
    hpcomware = "hpcomware"
    h3c = "h3c"
    alu = "alu"
    huaweiyang = "huaweiyang"
    huawei = "huawei"
    junos = "junos"
    csr = "csr"
    nexus = "nexus"
    iosxr = "iosxr"
    iosxe = "iosxe"


class NcclientDeviceParams(BaseModel):
    name: NcclientDeviceDrivers


class NcclientManagerParams(BaseModel):
    timeout: int


class NcclientConnection(BaseModel):
    host: str
    username: str
    password: str
    port: int
    hostkey_verify: bool
    device_params: Optional[NcclientDeviceParams] = None
    manager_params: Optional[NcclientManagerParams] = None


class NcclientGetArgs(BaseModel):
    filter: str
    render_json: bool = False


class NcclientSetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "library": "ncclient",
                    "connection_args": {
                        "host": "10.0.2.39",
                        "username": "admin",
                        "password": "admin",
                        "port": 830,
                        "hostkey_verify": False,
                    },
                    "args": {
                        "target": "running",
                        "config": "<nc:config xmlns:nc='urn:ietf:params:xml:ns:netconf:base:1.0'/>",
                        "render_json": True,
                    },
                    "queue_strategy": "fifo",
                }
            ]
        }
    )

    connection_args: NcclientConnection
    args: Optional[NcclientSendConfigArgs] = None
    j2config: Optional[J2Config] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None


class NcclientGetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "library": "ncclient",
                    "connection_args": {
                        "host": "10.0.2.39",
                        "username": "admin",
                        "password": "admin",
                        "port": 830,
                        "hostkey_verify": False,
                    },
                    "args": {
                        "source": "running",
                        "filter": "<filter type='subtree'><System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System></filter>",
                        "render_json": True,
                        "capabilities": True,
                    },
                    "queue_strategy": "fifo",
                    "cache": {"enabled": True, "ttl": 300, "poison": False},
                }
            ]
        }
    )

    connection_args: NcclientConnection
    args: Union[NcclientGetConfigArgs, NcclientGetRpcArgs]
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = None


class NcclientGet(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "library": "ncclient",
                    "connection_args": {
                        "host": "10.0.2.39",
                        "username": "admin",
                        "password": "admin",
                        "port": 830,
                        "hostkey_verify": False,
                    },
                    "args": {
                        "filter": "<filter type='subtree'><System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System></filter>",
                        "render_json": True,
                    },
                    "queue_strategy": "fifo",
                    "cache": {"enabled": True, "ttl": 300, "poison": False},
                }
            ]
        }
    )

    connection_args: NcclientConnection
    args: NcclientGetArgs
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = None

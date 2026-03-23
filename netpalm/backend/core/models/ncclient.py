from enum import Enum

from pydantic import BaseModel, ConfigDict

from netpalm.backend.core.models.models import (
    CacheConfig,
    J2Config,
    QueueStrategy,
    Webhook,
)


class NcclientSendConfigArgs(BaseModel):
    target: str | None = None
    config: str | None = None
    default_operation: str | None = None
    render_json: bool = False


class NcclientGetConfigArgs(BaseModel):
    source: str
    filter: str | None = None
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
    device_params: NcclientDeviceParams | None = None
    manager_params: NcclientManagerParams | None = None


class NcclientGetArgs(BaseModel):
    filter: str
    render_json: bool = False


class NcclientSetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    connection_args: NcclientConnection
    args: NcclientSendConfigArgs | None = None
    j2config: J2Config | None = None
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None


class NcclientGetConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    connection_args: NcclientConnection
    args: NcclientGetConfigArgs | NcclientGetRpcArgs
    webhook: Webhook | None = None
    queue_strategy: QueueStrategy | None = None
    cache: CacheConfig | None = None


class NcclientGet(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    connection_args: NcclientConnection
    args: NcclientGetArgs
    queue_strategy: QueueStrategy | None = None
    cache: CacheConfig | None = None

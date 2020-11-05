from typing import Optional, Union
from enum import Enum

from pydantic import BaseModel

from netpalm.backend.core.models.models import CacheConfig
from netpalm.backend.core.models.models import QueueStrategy
from netpalm.backend.core.models.models import Webhook
from netpalm.backend.core.models.models import J2Config


class NcclientSendConfigArgs(BaseModel):
    target: str
    default_operation: Optional[str] = None
    config: str


class NcclientGetConfigArgs(BaseModel):
    source: str
    filter: Optional[str] = None


class NcclientGetRpcArgs(BaseModel):
    rpc: str


class NcclientDeviceDrivers(str):
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


class NcclientConnection(BaseModel):
    host: str
    username: str
    password: str
    port: int
    hostkey_verify: bool
    device_params: Optional[NcclientDeviceParams] = None


class NcclientSetConfig(BaseModel):
    connection_args: NcclientConnection
    args: Optional[NcclientSendConfigArgs] = {}
    j2config: Optional[J2Config] = None
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    render_json: Optional[bool] = False

    class Config:
        schema_extra = {
            "example": {
                "library": "ncclient",
                "connection_args": {
                    "host": "10.0.2.39", "username": "admin", "password": "admin", "port": 830, "hostkey_verify": False
                },
                "render_json": True,
                "args": {
                    "target": "running",
                    "config": "<nc:config xmlns:nc='urn:ietf:params:xml:ns:netconf:base:1.0'><configure xmlns='http://www.cisco.com/nxos:1.0:vlan_mgr_cli'><__XML__MODE__exec_configure><interface><ethernet><interface>helloworld</interface><__XML__MODE_if-ethernet-switch><switchport><trunk><allowed><vlan><add><__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans><add-vlans>99</add-vlans></__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans></add></vlan></allowed></trunk></switchport></__XML__MODE_if-ethernet-switch></ethernet></interface></__XML__MODE__exec_configure></configure></nc:config>"
                },
                "queue_strategy": "pinned"
            }
        }


class NcclientGetConfig(BaseModel):
    connection_args: NcclientConnection
    args: Union[NcclientGetConfigArgs, NcclientGetRpcArgs]
    webhook: Optional[Webhook] = None
    queue_strategy: Optional[QueueStrategy] = None
    cache: Optional[CacheConfig] = {}
    render_json: Optional[bool] = False

    class Config:
        schema_extra = {
            "example": {
                "library": "ncclient",
                "connection_args": {
                    "host": "10.0.2.39", "username": "admin", "password": "admin", "port": 830, "hostkey_verify": False
                },
                "render_json": True,
                "args": {
                    "source": "running",
                    "filter": "<filter type='subtree'><System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System></filter>"
                },
                "queue_strategy": "fifo",
                "cache": {
                    "enabled": True,
                    "ttl": 300,
                    "poison": False
                }
            }
        }

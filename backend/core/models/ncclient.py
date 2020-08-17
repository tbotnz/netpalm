from typing import Optional

from pydantic import BaseModel

from backend.core.models.models import model_cache_config
from backend.core.models.models import model_webhook
from backend.core.models.models import queue_strat


class ncclient_send_config_args(BaseModel):
    target: str
    config: str

class ncclient_get_config_args(BaseModel):
    source: str
    filter: Optional[str] = None
    render_json:Optional[bool] = None

class model_ncclient_connection_args(BaseModel):
    host: str
    username: str
    password: str
    port: int
    hostkey_verify: bool

class model_ncclient_setconfig(BaseModel):
    connection_args: model_ncclient_connection_args
    args: ncclient_send_config_args
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[queue_strat] = None

    class Config:
        schema_extra = {
            "example": {
                "library": "ncclient",
                "connection_args": {
                    "host": "10.0.2.39", "username": "admin", "password": "admin", "port": 830, "hostkey_verify": False
                },
                "args": {
                    "target": "running",
                    "config": "<nc:config xmlns:nc='urn:ietf:params:xml:ns:netconf:base:1.0'><configure xmlns='http://www.cisco.com/nxos:1.0:vlan_mgr_cli'><__XML__MODE__exec_configure><interface><ethernet><interface>helloworld</interface><__XML__MODE_if-ethernet-switch><switchport><trunk><allowed><vlan><add><__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans><add-vlans>99</add-vlans></__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans></add></vlan></allowed></trunk></switchport></__XML__MODE_if-ethernet-switch></ethernet></interface></__XML__MODE__exec_configure></configure></nc:config>"
                },
                "queue_strategy": "pinned"
            }
        }

class model_ncclient_getconfig(BaseModel):
    connection_args: model_ncclient_connection_args
    args: ncclient_get_config_args
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[queue_strat] = None
    cache: Optional[model_cache_config] = {}

    class Config:
        schema_extra = {
            "example": {
                "library": "ncclient",
                "connection_args": {
                    "host": "10.0.2.39", "username": "admin", "password": "admin", "port": 830, "hostkey_verify": False
                },
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

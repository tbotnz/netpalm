import logging

from fastapi import APIRouter

# load models
from netpalm.backend.core.models.models import GetConfig
from netpalm.backend.core.models.napalm import NapalmGetConfig
from netpalm.backend.core.models.ncclient import NcclientGet
from netpalm.backend.core.models.ncclient import NcclientGetConfig
from netpalm.backend.core.models.netmiko import NetmikoGetConfig
from netpalm.backend.core.models.puresnmp import PureSNMPGetConfig
from netpalm.backend.core.models.restconf import Restconf
from netpalm.backend.core.models.task import Response

from netpalm.backend.core.manager import ntplm

from netpalm.routers.route_utils import error_handle_w_cache, whitelist

log = logging.getLogger(__name__)
router = APIRouter()


# read config
@router.post("/getconfig", response_model=Response, status_code=201)
@router.post("/get", response_model=Response, status_code=201)
@error_handle_w_cache
@whitelist
def get_config(getcfg: GetConfig):
    return ntplm._get_config(getcfg)


# read config
@router.post("/getconfig/netmiko", response_model=Response, status_code=201)
@router.post("/get/netmiko", response_model=Response, status_code=201)
@error_handle_w_cache
@whitelist
def get_config_netmiko(getcfg: NetmikoGetConfig):
    return ntplm.get_config_netmiko(getcfg)


# read config
@router.post("/getconfig/napalm", response_model=Response, status_code=201)
@router.post("/get/napalm", response_model=Response, status_code=201)
@error_handle_w_cache
@whitelist
def get_config_napalm(getcfg: NapalmGetConfig):
    return ntplm.get_config_napalm(getcfg)


# read config
@router.post("/getconfig/puresnmp", response_model=Response, status_code=201)
@router.post("/get/puresnmp", response_model=Response, status_code=201)
@error_handle_w_cache
@whitelist
def get_config_puresnmp(getcfg: PureSNMPGetConfig):
    return ntplm.get_config_puresnmp(getcfg)


# read config
@router.post("/getconfig/ncclient", response_model=Response, status_code=201)
@router.post("/get/ncclient", response_model=Response, status_code=201)
@error_handle_w_cache
@whitelist
def get_config_ncclient(getcfg: NcclientGetConfig):
    return ntplm.get_config_ncclient(getcfg)


# ncclient Manager.get() rpc call
# Certain device types dont have rpc methods defined in ncclient.
# This is a work around for that.
@router.post("/getconfig/ncclient/get",
             response_model=Response,
             status_code=201)
@router.post("/get/ncclient/get",
             response_model=Response,
             status_code=201)
@error_handle_w_cache
@whitelist
def ncclient_get(getcfg: NcclientGet, library: str = "ncclient"):
    return ntplm.ncclient_get(getcfg, library)


# read config
@router.post("/getconfig/restconf", response_model=Response, status_code=201)
@router.post("/get/restconf", response_model=Response, status_code=201)
@error_handle_w_cache
@whitelist
def get_config_restconf(getcfg: Restconf):
    return ntplm.get_config_restconf(getcfg)

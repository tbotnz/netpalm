import logging

from fastapi import APIRouter

# load models
from netpalm.backend.core.models.models import SetConfig
from netpalm.backend.core.models.napalm import NapalmSetConfig
from netpalm.backend.core.models.ncclient import NcclientSetConfig
from netpalm.backend.core.models.netmiko import NetmikoSetConfig
from netpalm.backend.core.models.restconf import Restconf
from netpalm.backend.core.models.task import Response

from netpalm.backend.core.manager import ntplm

from netpalm.routers.route_utils import HttpErrorHandler, poison_host_cache, whitelist

log = logging.getLogger(__name__)
router = APIRouter()


# deploy a configuration
@router.post("/setconfig", response_model=Response, status_code=201)
@HttpErrorHandler()
@poison_host_cache
@whitelist
def set_config(setcfg: SetConfig):
    return ntplm._set_config(setcfg)


# dry run a configuration
@router.post("/setconfig/dry-run", response_model=Response, status_code=201)
@HttpErrorHandler()
@whitelist
def set_config_dry_run(setcfg: SetConfig):
    return ntplm.set_config_dry_run(setcfg)


# deploy a configuration
@router.post("/setconfig/netmiko", response_model=Response, status_code=201)
@HttpErrorHandler()
@poison_host_cache
@whitelist
def set_config_netmiko(setcfg: NetmikoSetConfig):
    return ntplm.set_config_netmiko(setcfg)


# deploy a configuration
@router.post("/setconfig/napalm", response_model=Response, status_code=201)
@HttpErrorHandler()
@poison_host_cache
@whitelist
def set_config_napalm(setcfg: NapalmSetConfig):
    return ntplm.set_config_napalm(setcfg)


# deploy a configuration
@router.post("/setconfig/ncclient", response_model=Response, status_code=201)
@HttpErrorHandler()
@poison_host_cache
@whitelist
def set_config_ncclient(setcfg: NcclientSetConfig):
    return ntplm.set_config_ncclient(setcfg)


# deploy a configuration
@router.post("/setconfig/restconf", response_model=Response, status_code=201)
@HttpErrorHandler()
@poison_host_cache
@whitelist
def set_config_restconf(setcfg: Restconf):
    return ntplm.set_config_restconf(setcfg)

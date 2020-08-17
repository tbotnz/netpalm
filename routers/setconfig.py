from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

# load models
from backend.core.models.generic_models import GenericSetConfig
from backend.core.models.napalm import NapalmSetConfig
from backend.core.models.ncclient import NcclientSetConfig
from backend.core.models.netmiko import NetmikoSetConfig
from backend.core.models.restconf import Restconf
from backend.core.models.task import Response
from backend.core.redis import reds
from routers.route_utils import http_error_handler, poison_host_cache

router = APIRouter()


def _set_config(setcfg: GenericSetConfig, library: str = None):
    req_data = setcfg.dict()
    if library is not None:
        req_data["library"] = library
    r = reds.execute_task(method="setconfig", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp


# deploy a configuration
@router.post("/setconfig", response_model=Response, status_code=201)
@http_error_handler
@poison_host_cache
def set_config(setcfg: GenericSetConfig):
    return _set_config(setcfg)


# dry run a configuration
@router.post("/setconfig/dry-run", response_model=Response, status_code=201)
@http_error_handler
def set_config_dry_run(setcfg: GenericSetConfig):
    req_data = setcfg.dict()
    r = reds.execute_task(method="dryrun", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp


# deploy a configuration
@router.post("/setconfig/netmiko", response_model=Response, status_code=201)
@http_error_handler
@poison_host_cache
def set_config_netmiko(setcfg: NetmikoSetConfig):
    return _set_config(setcfg, library="netmiko")


# deploy a configuration
@router.post("/setconfig/napalm", response_model=Response, status_code=201)
@http_error_handler
@poison_host_cache
def set_config_napalm(setcfg: NapalmSetConfig):
    return _set_config(setcfg, library="napalm")


# deploy a configuration
@router.post("/setconfig/ncclient", response_model=Response, status_code=201)
@http_error_handler
@poison_host_cache
def set_config_ncclient(setcfg: NcclientSetConfig):
    return _set_config(setcfg, library="ncclient")


# deploy a configuration
@router.post("/setconfig/restconf", response_model=Response, status_code=201)
@http_error_handler
@poison_host_cache
def set_config_restconf(setcfg: Restconf):
    return _set_config(setcfg, library="restconf")

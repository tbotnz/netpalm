import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

# load models
from backend.core.models.generic_models import GetConfig
from backend.core.models.napalm import NapalmGetConfig
from backend.core.models.ncclient import NcclientGetConfig
from backend.core.models.netmiko import NetmikoGetConfig
from backend.core.models.restconf import Restconf
from backend.core.models.task import Response
from backend.core.redis import reds
from routers.route_utils import error_handle_w_cache

log = logging.getLogger(__name__)
router = APIRouter()


def _get_config(getcfg: GetConfig, library: str = None):
    req_data = getcfg.dict()
    if library is not None:
        req_data["library"] = library
    r = reds.execute_task(method="getconfig", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp


# read config
@router.post("/getconfig", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config(getcfg: GetConfig):
    return _get_config(getcfg)


# read config
@router.post("/getconfig/netmiko", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_netmiko(getcfg: NetmikoGetConfig):
    return _get_config(getcfg, library="netmiko")

#read config
@router.post("/getconfig/napalm", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_napalm(getcfg: NapalmGetConfig):
    return _get_config(getcfg, library="napalm")

#read config
@router.post("/getconfig/ncclient", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_ncclient(getcfg: NcclientGetConfig):
    return _get_config(getcfg, library="ncclient")

#read config
@router.post("/getconfig/restconf", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_restconf(getcfg: Restconf):
    return _get_config(getcfg, library="restconf")

import logging

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds

# load models
from backend.core.models.models import model_getconfig
from backend.core.models.netmiko import model_netmiko_getconfig
from backend.core.models.napalm import model_napalm_getconfig
from backend.core.models.ncclient import model_ncclient_getconfig
from backend.core.models.restconf import model_restconf
from backend.core.models.task import model_response
from routers.route_utils import cacheable_model, error_handle_w_cache

log = logging.getLogger(__name__)
router = APIRouter()


def _get_config(getcfg: model_getconfig, library: str = None):
    req_data = getcfg.dict()
    if library is not None:
        req_data["library"] = library
    r = reds.execute_task(method="getconfig", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp


# read config
@router.post("/getconfig", response_model=model_response, status_code=201)
@error_handle_w_cache
def get_config(getcfg: model_getconfig):
    return _get_config(getcfg)


# read config
@router.post("/getconfig/netmiko", response_model=model_response, status_code=201)
@error_handle_w_cache
def get_config_netmiko(getcfg: model_netmiko_getconfig):
    return _get_config(getcfg, library="netmiko")

#read config
@router.post("/getconfig/napalm", response_model=model_response, status_code=201)
@error_handle_w_cache
def get_config_napalm(getcfg: model_napalm_getconfig):
    return _get_config(getcfg, library="napalm")

#read config
@router.post("/getconfig/ncclient", response_model=model_response, status_code=201)
@error_handle_w_cache
def get_config_ncclient(getcfg: model_ncclient_getconfig):
    return _get_config(getcfg, library="ncclient")

#read config
@router.post("/getconfig/restconf", response_model=model_response, status_code=201)
@error_handle_w_cache
def get_config_restconf(getcfg: model_restconf):
    return _get_config(getcfg, library="restconf")

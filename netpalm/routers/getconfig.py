import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

# load models
from netpalm.backend.core.models.models import GetConfig
from netpalm.backend.core.models.napalm import NapalmGetConfig, NapalmGetConfigGetter
from netpalm.backend.core.models.ncclient import NcclientGet
from netpalm.backend.core.models.ncclient import NcclientGetConfig
from netpalm.backend.core.models.netmiko import NetmikoGetConfig
from netpalm.backend.core.models.puresnmp import PureSNMPGetConfig
from netpalm.backend.core.models.restconf import Restconf
from netpalm.backend.core.models.task import Response
from netpalm.backend.core.redis import reds
from netpalm.routers.route_utils import error_handle_w_cache

log = logging.getLogger(__name__)
router = APIRouter()


def _get_config(getcfg: GetConfig, library: str = None):
    req_data = getcfg.dict(exclude_none=True)
    if library is not None:
        req_data["library"] = library
    r = reds.execute_task(method="getconfig", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp


# read config
@router.post("/getconfig", response_model=Response, status_code=201)
@router.post("/get", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config(getcfg: GetConfig):
    return _get_config(getcfg)


# read config
@router.post("/getconfig/netmiko", response_model=Response, status_code=201)
@router.post("/get/netmiko", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_netmiko(getcfg: NetmikoGetConfig):
    return _get_config(getcfg, library="netmiko")


# read config
@router.post("/getconfig/napalm", response_model=Response, status_code=201)
@router.post("/get/napalm", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_napalm(getcfg: NapalmGetConfig):
    return _get_config(getcfg, library="napalm")


# read config
@router.post("/getconfig/puresnmp", response_model=Response, status_code=201)
@router.post("/get/puresnmp", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_puresnmp(getcfg: PureSNMPGetConfig):
    return _get_config(getcfg, library="puresnmp")


# read config
@router.post("/getconfig/ncclient", response_model=Response, status_code=201)
@router.post("/get/ncclient", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_ncclient(getcfg: NcclientGetConfig):
    return _get_config(getcfg, library="ncclient")


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
def ncclient_get(getcfg: NcclientGet, library: str = "ncclient"):
    req_data = getcfg.dict(exclude_none=True)
    if library is not None:
        req_data["library"] = library
    r = reds.execute_task(method="ncclient_get", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp


# read config
@router.post("/getconfig/restconf", response_model=Response, status_code=201)
@router.post("/get/restconf", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_restconf(getcfg: Restconf):
    return _get_config(getcfg, library="restconf")


@router.post("/napalm/getter/{getter}", response_model=Response, status_code=201)
@error_handle_w_cache
def get_config_napalm_getter(getter: str, getter_cfg: NapalmGetConfigGetter):
    """
    Attempt to use arbitrary NAPALM Getter to pull and process data.
    Subject to NAPALM platform support documented
    [here](https://napalm.readthedocs.io/en/latest/support/#getters-support-matrix).

    Example getter formats:

    -   /napalm/getter/arp-table
    -   /napalm/getter/get_arp_table
    -   /napalm/getter/get-arp-table

    all of those will ultimately call the NAPALM `get_arp_table` getter method.
    """
    getter = getter.replace('-', '_').replace(' ', '_').strip()
    if not getter.startswith('get_'):
        getter = f'get_{getter}'

    getcfg = GetConfig(
        library='napalm',
        command=getter,
        **getter_cfg.dict()
    )
    return _get_config(getcfg)

from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds

#load models
from backend.core.models.models import model_setconfig
from backend.core.models.netmiko import model_netmiko_setconfig
from backend.core.models.napalm import model_napalm_setconfig
from backend.core.models.ncclient import model_ncclient_setconfig
from backend.core.models.restconf import model_restconf
from backend.core.models.task import model_response

router = APIRouter()

#deploy a configuration
@router.post("/setconfig", response_model=model_response, status_code=201)
def set_config(setcfg: model_setconfig):
    try:
        req_data = setcfg.dict()
        r = reds.execute_task(method="setconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#dry run a configuration
@router.post("/setconfig/dry-run", response_model=model_response, status_code=201)
def set_config_dry_run(setcfg: model_setconfig):
    try:
        req_data = setcfg.dict()
        r = reds.execute_task(method="dryrun", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#deploy a configuration
@router.post("/setconfig/netmiko", response_model=model_response, status_code=201)
def set_config_netmiko(setcfg: model_netmiko_setconfig):
    try:
        req_data = setcfg.dict()
        r = reds.execute_task(method="setconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#deploy a configuration
@router.post("/setconfig/napalm", response_model=model_response, status_code=201)
def set_config_napalm(setcfg: model_napalm_setconfig):
    try:
        req_data = setcfg.dict()
        r = reds.execute_task(method="setconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#deploy a configuration
@router.post("/setconfig/ncclient", response_model=model_response, status_code=201)
def set_config_ncclient(setcfg: model_ncclient_setconfig):
    try:
        req_data = setcfg.dict()
        r = reds.execute_task(method="setconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#deploy a configuration
@router.post("/setconfig/restconf", response_model=model_response, status_code=201)
def set_config_restconf(setcfg: model_restconf):
    try:
        req_data = setcfg.dict()
        r = reds.execute_task(method="setconfig", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

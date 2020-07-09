from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds

#load models
from backend.core.models.models import model_getconfig, model_response
from backend.core.models.netmiko import model_netmiko_getconfig
from backend.core.models.napalm import model_napalm_getconfig
from backend.core.models.ncclient import model_ncclient_getconfig
from backend.core.models.restconf import model_restconf

router = APIRouter()

#read config
@router.post("/getconfig", response_model=model_response, status_code=201)
async def get_config(getcfg: model_getconfig):
  try:
    req_data = getcfg.dict()
    r = reds.execute_task(method="getconfig",kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#read config
@router.post("/getconfig/netmiko", response_model=model_response, status_code=201)
async def get_config_netmiko(getcfg: model_netmiko_getconfig):
  try:
    req_data = getcfg.dict()
    r = reds.execute_task(method="getconfig",kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#read config
@router.post("/getconfig/napalm", response_model=model_response, status_code=201)
async def get_config_napalm(getcfg: model_napalm_getconfig):
  try:
    req_data = getcfg.dict()
    r = reds.execute_task(method="getconfig",kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#read config
@router.post("/getconfig/ncclient", response_model=model_response, status_code=201)
async def get_config_ncclient(getcfg: model_ncclient_getconfig):
  try:
    req_data = getcfg.dict()
    r = reds.execute_task(method="getconfig",kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#read config
@router.post("/getconfig/restconf", response_model=model_response, status_code=201)
async def get_config_restconf(getcfg: model_restconf):
  try:
    req_data = getcfg.dict()
    r = reds.execute_task(method="getconfig",kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

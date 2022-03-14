import importlib

import inspect

import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel

from netpalm.backend.core.confload.confload import config
# load models
from netpalm.backend.core.models.models import Script, ScriptCustom
from netpalm.backend.core.models.task import Response
from netpalm.backend.core.models.task import ResponseBasic

from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

from netpalm.backend.core.manager import ntplm

from netpalm.backend.plugins.calls.scriptrunner.script import script_model_finder

from netpalm.routers.route_utils import error_handle_w_cache

router = APIRouter()

log = logging.getLogger(__name__)

# get template list
@router.get("/script", response_model=ResponseBasic)
@HttpErrorHandler()
async def list_scripts():
    r = routes["ls"](fldr="script")
    resp = jsonable_encoder(r)
    return resp


@router.post("/script", response_model=Response, status_code=201)
@error_handle_w_cache
def execute_script(script: Script):
    if isinstance(script, dict):
        req_data = script
    else:
        req_data = script.dict(exclude_none=True)
    return ntplm.execute_script(**req_data)

r = routes["ls"](fldr="script")
for script in r["data"]["task_result"]["templates"]:
    model = script_model_finder(script_name=script)[0]
    
    @router.post(f"/script/v1/{script}", response_model=Response, status_code=201)
    @error_handle_w_cache
    def execute_script(script: model):
        if isinstance(script, dict):
            req_data = script
        else:
            req_data = script.dict(exclude_none=True)
        return ntplm.execute_script(**req_data)

# get template list
@router.get("/webhook", response_model=ResponseBasic)
@HttpErrorHandler()
async def list_webhooks():
    r = routes["ls"](fldr="webhook_script")
    resp = jsonable_encoder(r)
    return resp

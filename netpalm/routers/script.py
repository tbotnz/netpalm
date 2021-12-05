import importlib
import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.confload.confload import config
# load models
from netpalm.backend.core.models.models import Script
from netpalm.backend.core.models.task import Response
from netpalm.backend.core.models.task import ResponseBasic

from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

from netpalm.backend.core.manager import ntplm

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
@HttpErrorHandler()
def execute_script(script: Script):
    return ntplm.execute_script(script)

r = routes["ls"](fldr="script")
for script in r["data"]["task_result"]["templates"]:
    try:
        model_name = f"{script}_model"
        template_model_path_raw = config.custom_scripts
        template_model_path = template_model_path_raw.replace('/', '.') + model_name
        module = importlib.import_module(template_model_path)
        model = getattr(module, model_name)
    except Exception as e:
        log.info(f"dynamic_script_route: no model found for {script} import error {e}")
        model = Script


    @router.post(f"/script/v1/{script}", response_model=Response, status_code=201)
    @HttpErrorHandler()
    def execute_script(script: model):
        return ntplm.execute_script(script)

# get template list
@router.get("/webhook", response_model=ResponseBasic)
@HttpErrorHandler()
async def list_webhooks():
    r = routes["ls"](fldr="webhook_script")
    resp = jsonable_encoder(r)
    return resp

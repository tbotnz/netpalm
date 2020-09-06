import importlib
import logging

from fastapi import APIRouter, Request, HTTPException
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.confload.confload import config
# load models
from netpalm.backend.core.models.service import model_service
from netpalm.backend.core.models.task import ServiceResponse
from netpalm.backend.core.redis import reds
# load routes
from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/service/{servicename}", response_model=ServiceResponse, status_code=201)
@HttpErrorHandler()
def create_service_instance(servicename: str, service: model_service):
    req_data = service.dict()
    req_data["netpalm_service_name"] = servicename
    r = reds.execute_service_task(metho="render_service", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp

@router.get("/service/instance/{service_id}")
def fetch_service_instance(service_id: str):
    r = reds.fetch_service_instance_args(sid=service_id)
    if r:
        resp = jsonable_encoder(r)
        return resp
    else:
        raise HTTPException(status_code=204, detail=f"{service_id} not found")

@router.post("/service/instance/validate/{service_id}")
@HttpErrorHandler()
def validate_service_instance_state(service_id: str):
    r = reds.validate_service_instance(sid=service_id)
    resp = jsonable_encoder(r)
    return resp

@router.post("/service/instance/re-deploy/{service_id}")
@HttpErrorHandler()
def redeploy_service_instance_state(service_id: str):
    r = reds.redeploy_service_instance(sid=service_id)
    resp = jsonable_encoder(r)
    return resp

@router.post("/service/instance/delete/{service_id}")
@HttpErrorHandler()
def delete_service_instance_state(service_id: str):
    r = reds.delete_service_instance(sid=service_id)
    resp = jsonable_encoder(r)
    return resp

r = routes["ls"](fldr="service")
for servicename in r["data"]["task_result"]["templates"]:
    try:
        model_name = f"{servicename}_model"
        template_model_path_raw = config.jinja2_service_templates
        template_model_path = template_model_path_raw.replace('/', '.') + model_name
        module = importlib.import_module(template_model_path)
        model = getattr(module, model_name)
    except Exception as e:
        log.error(f"dynamic_service_route: no model found for {servicename} import error {e}")
        model = model_service


    @router.post(f"/service/v1/{servicename}", response_model=ServiceResponse, status_code=201)
    @HttpErrorHandler()
    def create_service_instance(service: model, request: Request):
        service_name = f"{request.url}".split('/')[-1]
        req_data = service.dict()
        req_data["netpalm_service_name"] = service_name
        r = reds.execute_service_task(method="render_service", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

import importlib
import logging

from fastapi import APIRouter, Request, HTTPException

from netpalm.backend.core.confload.confload import config

# load models
from netpalm.backend.core.models.service import ServiceModel, ServiceInventoryResponse
from netpalm.backend.core.models.task import ServiceResponse, Response

from netpalm.backend.core.manager import ntplm

# load routes
from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/service/{service_model}", response_model=ServiceResponse, status_code=201)
@HttpErrorHandler()
def create_service_instance(service_model: str, service: ServiceModel):
    return ntplm.create_new_service_instance(service_model, service)


@router.get("/service/instances/", response_model=ServiceInventoryResponse)
@HttpErrorHandler()
def list_service_instances():
    return ntplm.list_service_instances()


@router.get("/service/instance/{service_id}")
@HttpErrorHandler()
def get_service_instance(service_id: str):
    res = ntplm.get_service_instance(service_id)
    if res:
        return res
    else:
        raise HTTPException(status_code=204, detail=f"{service_id} not found")


@router.post("/service/instance/validate/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def validate_service_instance_state(service_id: str):
    return ntplm.validate_service_instance_state(service_id)


@router.post("/service/instance/retrieve/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def retrieve_service_instance_state(service_id: str):
    return ntplm.retrieve_service_instance_state(service_id)


@router.post("/service/instance/re-deploy/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def redeploy_service_instance_state(service_id: str):
    return ntplm.redeploy_service_instance_state(service_id)


@router.post("/service/instance/delete/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def delete_service_instance_state(service_id: str):
    return ntplm.delete_service_instance_state(service_id)


r = routes["ls"](fldr="service")
for service_model in r["data"]["task_result"]["templates"]:
    try:
        model_name = f"{service_model}_model"
        template_model_path_raw = config.jinja2_service_templates
        template_model_path = template_model_path_raw.replace('/', '.') + model_name
        module = importlib.import_module(template_model_path)
        model = getattr(module, model_name)
    except Exception as e:
        log.error(f"dynamic_service_route: no model found for {service_model} import error {e}")
        model = ServiceModel


    @router.post(f"/service/v1/{service_model}", response_model=ServiceResponse, status_code=201)
    @HttpErrorHandler()
    def create_service_instance(service: model, request: Request):
        # url hack
        service_model_name = f"{request.url}".split('/')[-1]
        return ntplm.create_new_service_instance(service_model_name, service)

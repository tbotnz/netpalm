import importlib
import inspect

from typing import Any

import logging

from pydantic import BaseModel

from fastapi import APIRouter, Request, HTTPException

from netpalm.backend.core.confload.confload import config

# load models
from netpalm.backend.core.models.service import ServiceModel, ServiceInventoryResponse
from netpalm.backend.core.models.task import ServiceResponse, Response

from netpalm.backend.core.manager import ntplm


from netpalm.backend.plugins.calls.service.procedures import get_service

# load routes
from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

router = APIRouter()

log = logging.getLogger(__name__)


#@router.get("/service/instances/", response_model=ServiceInventoryResponse)
@router.get("/service/instances/")
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


r = routes["ls"](fldr="service")
for service_model in r["data"]["task_result"]["templates"]:
    try:
        model_name = f"{service_model}"
        model = get_service(model_name)["service_model"]
    except Exception as e:
        log.error(f"dynamic_service_route: no model found for {service_model} import error {e}")
        model = ServiceModel


    @router.post(f"/service/instance/create/{service_model}", response_model=ServiceResponse, status_code=201)
    @HttpErrorHandler()
    def create_service_instance(service: model, request: Request):
        # url hack
        service_model_name = f"{request.url.path}".split('/')[-1]
        return ntplm.create_new_service_instance(service_model_name, service)

    @router.patch(f"/service/instance/update/{service_model}"+"/{service_id}", response_model=Response, status_code=201)
    @HttpErrorHandler()
    def update_service_instance_state(service: model, service_id: str, request: Request):
        return ntplm.update_service_instance(service_id, service)

@router.delete("/service/instance/delete/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def delete_service_instance_state(service_id: str):
    return ntplm.delete_service_instance_state(service_id)

@router.post("/service/instance/redeploy/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def redeploy_service_instance_state(service_id: str):
    return ntplm.redeploy_service_instance_state(service_id)

@router.post("/service/instance/validate/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def validate_service_instance_state(service_id: str):
    return ntplm.validate_service_instance_state(service_id)

@router.post("/service/instance/healthcheck/{service_id}", response_model=Response, status_code=201)
@HttpErrorHandler()
def health_check_service_instance_state(service_id: str):
    return ntplm.health_check_service_instance_state(service_id)

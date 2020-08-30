import importlib
import logging

from fastapi import APIRouter, Request
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.confload.confload import config
# load models
from netpalm.backend.core.models.service import model_service
from netpalm.backend.core.models.task import Response
from netpalm.backend.core.redis import reds
# load routes
from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

router = APIRouter()

log = logging.getLogger(__name__)


@router.post("/service/{servicename}", response_model=Response, status_code=201)
@HttpErrorHandler()
def execute_service_legacy(servicename: str, service: model_service):
    req_data = service.dict()
    req_data["netpalm_service_name"] = servicename
    r = reds.execute_task(method="render_service", kwargs=req_data)
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


    @router.post(f"/service/v1/{servicename}", response_model=Response, status_code=201)
    @HttpErrorHandler()
    def execute_service(service: model, request: Request):
        service_name = f"{request.url}".split('/')[-1]
        req_data = service.dict()
        req_data["netpalm_service_name"] = service_name
        r = reds.execute_task(method="render_service", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp

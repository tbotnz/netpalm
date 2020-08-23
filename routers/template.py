import logging

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

# load models
from backend.core.models.models import TemplateRemove, TemplateAdd
from backend.core.models.task import ResponseBasic
from backend.core.models.transaction_log import TransactionLogEntryType
# load routes
from backend.core.routes.routes import routes
from routers.route_utils import HttpErrorHandler, add_transaction_log_entry

log = logging.getLogger(__name__)
router = APIRouter()


# textfsm template routes
@router.get("/template", response_model=ResponseBasic)
@HttpErrorHandler()
async def get_textfsm_template():
    r = routes["gettemplate"]()
    resp = jsonable_encoder(r)
    return resp


@router.post("/template", response_model=ResponseBasic, status_code=201)
@HttpErrorHandler()
async def add_textfsm_template(template_add: TemplateAdd):
    req_data = template_add.dict()
    log.debug(req_data)
    resp = routes["addtemplate"](**req_data)
    add_transaction_log_entry(entry_type=TransactionLogEntryType.tfsm_pull, data=req_data)
    return resp


@router.delete("/template", status_code=204)
@HttpErrorHandler()
async def delete_textfsm_template(template_remove: TemplateRemove):
    req_data = template_remove.dict()
    r = routes["removetemplate"](**req_data)
    try:
        req_data["fsm_template"] = req_data.pop("template")
    except KeyError:
        pass

    add_transaction_log_entry(entry_type=TransactionLogEntryType.tfsm_delete, data=req_data)
    return r

#j2 routes

# get template list
@router.get("/j2template/config/", response_model=ResponseBasic)
async def get_config_j2_templates():
    try:
        r = routes["ls"](fldr="config")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))


@router.get("/j2template/service/", response_model=ResponseBasic)
async def get_service_j2_templates():
    try:
        r = routes["ls"](fldr="service")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.get("/j2template/webhook/", response_model=ResponseBasic)
async def get_webhook_j2_templates():
    try:
        r = routes["ls"](fldr="webhook")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#view contents of a template
@router.get("/j2template/config/{tmpname}", response_model=ResponseBasic)
async def get_j2_template_specific_config(tmpname: str):
    try:
        r = routes["j2gettemplate"](tmpname, template_type="config")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.get("/j2template/service/{tmpname}", response_model=ResponseBasic)
async def get_j2_template_specific_service(tmpname: str):
    try:
        r = routes["j2gettemplate"](tmpname, template_type="service")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.get("/j2template/webhook/{tmpname}", response_model=ResponseBasic)
async def get_j2_template_specific_webhook(tmpname: str):
    try:
        r = routes["j2gettemplate"](tmpname, template_type="webhook")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#render j2 templates
@router.post("/j2template/render/config/{tmpname}", response_model=ResponseBasic, status_code=201)
async def render_j2_template_config(tmpname: str, data: dict):
    try:
        req_data = data
        r = routes["render_j2template"](tmpname, template_type="config", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.post("/j2template/render/service/{tmpname}", response_model=ResponseBasic, status_code=201)
async def render_j2_template_service(tmpname: str, data: dict):
    try:
        req_data = data
        r = routes["render_j2template"](tmpname, template_type="service", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.post("/j2template/render/webhook/{tmpname}", response_model=ResponseBasic, status_code=201)
async def render_j2_template_webhook(tmpname: str, data: dict):
    try:
        req_data = data
        r = routes["render_j2template"](tmpname, template_type="webhook", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

import logging
from pathlib import Path
from typing import Union
import copy

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from textfsm.clitable import CliTable, IndexTable

from netpalm.backend.core.confload.confload import config
# load models
from netpalm.backend.core.models.models import TFSMTemplateRemove, TFSMTemplateAdd, TFSMPushTemplateModel, \
    TFSMTemplateMatch, TFSMTemplateMatchResponse, UnivsersalTemplateAdd, UnivsersalTemplateRemove
from netpalm.backend.core.models.task import ResponseBasic
from netpalm.backend.core.models.transaction_log import TransactionLogEntryType
# load routes
from netpalm.backend.core.routes.routes import routes
from netpalm.backend.plugins.utilities.textfsm.template import FSMTemplate
from netpalm.backend.plugins.utilities.universal_template_mgr.unvrsl import unvrsl
from netpalm.routers.route_utils import HttpErrorHandler, add_transaction_log_entry

log = logging.getLogger(__name__)
router = APIRouter()


# textfsm template routes
@router.get("/template", response_model=ResponseBasic)
@HttpErrorHandler()
async def list_textfsm_templates():
    r = routes["listtemplates"]()
    resp = jsonable_encoder(r)
    return resp


# view contents of a template
@router.get("/template/{tmpname}", response_model=ResponseBasic)
@HttpErrorHandler()
async def get_textfsm_template(tmpname: str):
    r = routes["gettemplate"](template=tmpname)
    resp = jsonable_encoder(r)
    return resp


@router.post("/template", response_model=ResponseBasic, status_code=201)
@HttpErrorHandler()
async def add_textfsm_template(template_add: Union[TFSMTemplateAdd, TFSMPushTemplateModel]):
    req_data = template_add.dict()
    if isinstance(template_add, TFSMTemplateAdd):
        entry_type = TransactionLogEntryType.tfsm_pull
        template_obj = FSMTemplate(**req_data)
        template_text = template_obj.fetch_template()
        req_data["template_text"] = template_text
        req_data.pop("key")

    entry_type = TransactionLogEntryType.tfsm_push
    log.debug(f"{entry_type=}")
    resp = routes["pushtemplate"](**req_data)

    add_transaction_log_entry(entry_type=entry_type, data=req_data)
    return resp


@router.post('/template/match', response_model=TFSMTemplateMatchResponse)
@HttpErrorHandler()
async def match_textfsm_templates(template_match: TFSMTemplateMatch):
    attrs = {
        'Command': template_match.command,
        'Platform': template_match.driver
    }
    tfsm_index_file = config.txtfsm_index_file
    # can we move this into a utility or something @Will?
    # accesses TextFSM internals because there's no other option
    # TFSM Internals assume that there might be more than one template match.  I'm not sure when that would be the
    # case, or why it would be useful, but I'm honoring that here as well.

    cli_table = CliTable(index_file=config.txtfsm_index_file, template_dir=Path(tfsm_index_file).parent)
    index: IndexTable = cli_table.index
    row_idx = index.GetRowMatch(attrs)
    if not row_idx:
        raise ValueError(f'No template found for {attrs}')

    template_details = cli_table.index.index[row_idx]

    template_details['template_text'] = ''

    template_file_handles = []  # I don't like this, but this seems to be the only way given how TFSM works :'(

    try:
        template_file_handles = cli_table._TemplateNamesToFiles(template_details['Template'])
        for f in template_file_handles:
            template_details['template_text'] += f.read()
    finally:
        for f in template_file_handles:
            f.close()

    return template_details


@router.delete("/template", status_code=204)
@HttpErrorHandler()
async def delete_textfsm_template(template_remove: TFSMTemplateRemove):
    req_data = template_remove.dict()
    r = routes["removetemplate"](**req_data)
    try:
        req_data["fsm_template"] = req_data.pop("template")
    except KeyError:
        pass

    add_transaction_log_entry(entry_type=TransactionLogEntryType.tfsm_delete, data=req_data)
    return r

# j2 routes

# get template list
@router.get("/ttptemplate/", response_model=ResponseBasic)
async def list_ttp_templates():
    try:
        r = routes["ls"](fldr="ttp_templates")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))


# get a specfic template
@router.get("/ttptemplate/{tmpname}", response_model=ResponseBasic)
async def return_specific_ttp_template(tmpname: str):
    try:
        send_payload = {
            "route_type": "ttp_templates",
            "name": tmpname
        }
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.get_template(payload=send_payload)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))


# add j2 config template
@router.post("/ttptemplate/", response_model=ResponseBasic)
def add_ttp_template(template: UnivsersalTemplateAdd):
    try:
        req_data = template.dict()
        req_data["route_type"] = "ttp_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_push, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.add_template(payload=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# remove j2 config template
@router.delete("/ttptemplate/", status_code=204)
def remove_ttp_template(template: UnivsersalTemplateRemove):
    try:
        req_data = template.dict()
        req_data["route_type"] = "ttp_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_delete, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.remove_template(payload=req_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

@router.get("/j2template/config/", response_model=ResponseBasic)
async def list_config_j2_templates():
    try:
        r = routes["ls"](fldr="config")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# get a specfic template
@router.get("/j2template/config/{tmpname}", response_model=ResponseBasic)
async def return_specific_config_j2_template(tmpname: str):
    try:
        send_payload = {
            "route_type": "j2_config_templates",
            "name": tmpname
        }
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.get_template(payload=send_payload)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# add j2 config template
@router.post("/j2template/config/", response_model=ResponseBasic)
def add_config_j2_templates(template: UnivsersalTemplateAdd):
    try:
        req_data = template.dict()
        req_data["route_type"] = "j2_config_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_push, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.add_template(payload=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# remove j2 config template
@router.delete("/j2template/config/", status_code=204)
def remove_config_j2_templates(template: UnivsersalTemplateRemove):
    try:
        req_data = template.dict()
        req_data["route_type"] = "j2_config_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_delete, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.remove_template(payload=req_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# get j2 service templates
@router.get("/template/service/", response_model=ResponseBasic)
async def list_service_templates():
    try:
        r = routes["ls"](fldr="service")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

# get a specfic template
@router.get("/template/service/{tmpname}", response_model=ResponseBasic)
async def return_specific_service_template(tmpname: str):
    try:
        send_payload = {
            "route_type": "j2_service_templates",
            "name": tmpname
        }
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.get_template(payload=send_payload)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# add j2 service template
@router.post("/template/service/", response_model=ResponseBasic)
def add_service_templates(template: UnivsersalTemplateAdd):
    try:
        req_data = template.dict()
        req_data["route_type"] = "j2_service_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_push, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.add_template(payload=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# remove j2 service template
@router.delete("/template/service/", status_code=204)
def remove_service_templates(template: UnivsersalTemplateRemove):
    try:
        req_data = template.dict()
        req_data["route_type"] = "j2_service_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_delete, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.remove_template(payload=req_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# get j2 webhook templates
@router.get("/j2template/webhook/", response_model=ResponseBasic)
async def list_webhook_j2_templates():
    try:
        r = routes["ls"](fldr="webhook")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

# get a specfic template
@router.get("/j2template/webhook/{tmpname}", response_model=ResponseBasic)
async def return_specific_webhook_j2_template(tmpname: str):
    try:
        send_payload = {
            "route_type": "j2_webhook_templates",
            "name": tmpname
        }
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.get_template(payload=send_payload)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# add j2 webhook template
@router.post("/j2template/webhook/", response_model=ResponseBasic)
def add_webhook_j2_templates(template: UnivsersalTemplateAdd):
    try:
        req_data = template.dict()
        req_data["route_type"] = "j2_webhook_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_push, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.add_template(payload=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# remove j2 webhook template
@router.delete("/j2template/webhook/", status_code=204)
def remove_webhook_j2_templates(template: UnivsersalTemplateRemove):
    try:
        req_data = template.dict()
        req_data["route_type"] = "j2_webhook_templates"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_delete, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.remove_template(payload=req_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# view contents of a config template
@router.get("/j2template/config/{tmpname}", response_model=ResponseBasic)
async def get_j2_template_specific_config(tmpname: str):
    try:
        r = routes["j2gettemplate"](tmpname, template_type="config")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

# # view contents of a service template
# @router.get("/j2template/service/{tmpname}", response_model=ResponseBasic)
# async def get_j2_template_specific_service(tmpname: str):
#     try:
#         r = routes["j2gettemplate"](tmpname, template_type="service")
#         resp = jsonable_encoder(r)
#         return resp
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e).split('\n'))

# view contents of a webhook template
@router.get("/j2template/webhook/{tmpname}", response_model=ResponseBasic)
async def get_j2_template_specific_webhook(tmpname: str):
    try:
        r = routes["j2gettemplate"](tmpname, template_type="webhook")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

# render contents of a config template
@router.post("/j2template/render/config/{tmpname}", response_model=ResponseBasic, status_code=201)
async def render_j2_template_config(tmpname: str, data: dict):
    try:
        req_data = data
        r = routes["render_j2template"](tmpname, template_type="config", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

# # render contents of a service template
# @router.post("/j2template/render/service/{tmpname}", response_model=ResponseBasic, status_code=201)
# async def render_j2_template_service(tmpname: str, data: dict):
#     try:
#         req_data = data
#         r = routes["render_j2template"](tmpname, template_type="service", kwargs=req_data)
#         resp = jsonable_encoder(r)
#         return resp
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e).split('\n'))

# render contents of a webhook template
@router.post("/j2template/render/webhook/{tmpname}", response_model=ResponseBasic, status_code=201)
async def render_j2_template_webhook(tmpname: str, data: dict):
    try:
        req_data = data
        r = routes["render_j2template"](tmpname, template_type="webhook", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

# move this section in the future but i'm tired

# add script file
@router.post("/script/add/", response_model=ResponseBasic)
def add_script_file(template: UnivsersalTemplateAdd):
    try:
        req_data = template.dict()
        req_data["route_type"] = "custom_scripts"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_push, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.add_template(payload=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# remove script file
@router.delete("/script/remove/", status_code=204)
def remove_script_file(template: UnivsersalTemplateRemove):
    try:
        req_data = template.dict()
        req_data["route_type"] = "custom_scripts"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_delete, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.remove_template(payload=req_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# get a specfic template
@router.get("/script/{tmpname}", response_model=ResponseBasic)
async def return_specific_script_file(tmpname: str):
    try:
        send_payload = {
            "route_type": "custom_scripts",
            "name": tmpname
        }
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.get_template(payload=send_payload)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# webhook script file
@router.post("/webhook/add/", response_model=ResponseBasic)
def add_webhook_script_file(template: UnivsersalTemplateAdd):
    try:
        req_data = template.dict()
        req_data["route_type"] = "custom_webhooks"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_push, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.add_template(payload=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# get a specfic template
@router.get("/webhook/{tmpname}", response_model=ResponseBasic)
async def return_specific_webhook_script_file(tmpname: str):
    try:
        send_payload = {
            "route_type": "custom_webhooks",
            "name": tmpname
        }
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.get_template(payload=send_payload)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

# remove script file
@router.delete("/webhook/remove/", status_code=204)
def remove_webhook_script_file(template: UnivsersalTemplateRemove):
    try:
        req_data = template.dict()
        req_data["route_type"] = "custom_webhooks"
        add_transaction_log_entry(entry_type=TransactionLogEntryType.unvrsl_tmp_delete, data=req_data)
        tmplate_mgr = unvrsl()
        r = tmplate_mgr.remove_template(payload=req_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))
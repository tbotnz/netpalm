import json

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

# load models
from backend.core.models.models import model_template_remove, model_template_add
from backend.core.models.task import model_response_basic
from backend.core.redis import reds
# load routes
from backend.core.routes.routes import routes

router = APIRouter()


# textfsm template routes
@router.get("/template", response_model=model_response_basic)
async def get_textfsm_template():
	try:
		r = routes["gettemplate"]()
		worker_message = {
		'type': 'get_textfsm_template',
		'kwargs': {}
		}
		reds.send_broadcast(json.dumps(worker_message))
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.post("/template", response_model=model_response_basic, status_code=201)
async def add_textfsm_template(template_add: model_template_add):
	try:
		req_data = template_add.dict()
		r = routes["addtemplate"](kwargs=req_data)
		resp = jsonable_encoder(r)
		worker_message = {
		'type': 'add_textfsm_template',
		'kwargs': req_data
		}
		reds.send_broadcast(json.dumps(worker_message))
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.delete("/template", status_code=204)
async def delete_textfsm_template(template_remove: model_template_remove):
	try:
		req_data = template_remove.dict()
		r = routes["removetemplate"](kwargs=req_data)
		resp = jsonable_encoder(r)
		worker_message = {
		'type': 'delete_textfsm_template',
		'kwargs': req_data
		}
		reds.send_broadcast(json.dumps(worker_message))
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

#j2 routes

# get template list
@router.get("/j2template/config/", response_model=model_response_basic)
async def get_config_j2_templates():
	try:
		r = routes["ls"](fldr="config")
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.get("/j2template/service/", response_model=model_response_basic)
async def get_service_j2_templates():
	try:
		r = routes["ls"](fldr="service")
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.get("/j2template/webhook/", response_model=model_response_basic)
async def get_webhook_j2_templates():
	try:
		r = routes["ls"](fldr="webhook")
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

#view contents of a template
@router.get("/j2template/config/{tmpname}", response_model=model_response_basic)
async def get_j2_template_specific_config(tmpname: str):
	try:
		r = routes["j2gettemplate"](tmpname, template_type="config")
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.get("/j2template/service/{tmpname}", response_model=model_response_basic)
async def get_j2_template_specific_service(tmpname: str):
	try:
		r = routes["j2gettemplate"](tmpname, template_type="service")
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.get("/j2template/webhook/{tmpname}", response_model=model_response_basic)
async def get_j2_template_specific_webhook(tmpname: str):
	try:
		r = routes["j2gettemplate"](tmpname, template_type="webhook")
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

#render j2 templates
@router.post("/j2template/render/config/{tmpname}", response_model=model_response_basic, status_code=201)
async def render_j2_template_config(tmpname: str, data: dict):
	try:
		req_data = data
		r = routes["render_j2template"](tmpname, template_type="config", kwargs=req_data)
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.post("/j2template/render/service/{tmpname}", response_model=model_response_basic, status_code=201)
async def render_j2_template_service(tmpname: str, data: dict):
	try:
		req_data = data
		r = routes["render_j2template"](tmpname, template_type="service", kwargs=req_data)
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.post("/j2template/render/webhook/{tmpname}", response_model=model_response_basic, status_code=201)
async def render_j2_template_webhook(tmpname: str, data: dict):
	try:
		req_data = data
		r = routes["render_j2template"](tmpname, template_type="webhook", kwargs=req_data)
		resp = jsonable_encoder(r)
		return resp
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e).split('\n'))
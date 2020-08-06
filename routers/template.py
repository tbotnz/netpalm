from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

#load routes
from backend.core.routes.routes import routes

#load models
from backend.core.models.models import model_template_remove, model_template_add
from backend.core.models.task import model_response_basic

router = APIRouter()

#text fsmtemplate routes
@router.get("/template", response_model=model_response_basic)
async def get_j2_template():
  try:
    r = routes["gettemplate"]()
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.post("/template", response_model=model_response_basic ,status_code=201)
async def add_template(template_add: model_template_add):
  try:
    req_data = template_add.dict()
    r = routes["addtemplate"](kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.post("/template", status_code=204)
async def delete_j2_template(template_remove: model_template_remove):
  try:
      req_data = template_remove.dict()
      r = routes["removetemplate"](kwargs=req_data)
      resp = jsonable_encoder(r)
      return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#j2 routes

# get template list
@router.get("/j2template/config/", response_model=model_response_basic)
async def get_config_j2_templates():
  try:
    r = routes["j2gettemplates"](template_type="config")
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.get("/j2template/service/", response_model=model_response_basic)
async def get_service_j2_templates():
  try:
    r = routes["j2gettemplates"](template_type="service")
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.get("/j2template/webhook/", response_model=model_response_basic)
async def get_webhook_j2_templates():
  try:
    r = routes["j2gettemplates"](template_type="webhook")
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#view contents of a template
@router.get("/j2template/config/{tmpname}", response_model=model_response_basic)
async def get_j2_template_specific_config(tmpname: str):
  try:
      r = routes["j2gettemplate"](tmpname, template_type="config")
      resp = jsonable_encoder(r)
      return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.get("/j2template/service/{tmpname}", response_model=model_response_basic)
async def get_j2_template_specific_service(tmpname: str):
  try:
      r = routes["j2gettemplate"](tmpname, template_type="service")
      resp = jsonable_encoder(r)
      return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.get("/j2template/webhook/{tmpname}", response_model=model_response_basic)
async def get_j2_template_specific_webhook(tmpname: str):
  try:
      r = routes["j2gettemplate"](tmpname, template_type="webhook")
      resp = jsonable_encoder(r)
      return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

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
    pass

@router.post("/j2template/render/service/{tmpname}", response_model=model_response_basic, status_code=201)
async def render_j2_template_service(tmpname: str, data: dict):
  try:
    req_data = data
    r = routes["render_j2template"](tmpname, template_type="service", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.post("/j2template/render/webhook/{tmpname}", response_model=model_response_basic, status_code=201)
async def render_j2_template_webhook(tmpname: str, data: dict):
  try:
    req_data = data
    r = routes["render_j2template"](tmpname, template_type="webhook", kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass
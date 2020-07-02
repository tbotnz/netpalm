from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

#load routes
from backend.core.routes.routes import routes

#load models
from backend.core.models.models import model_template_remove, model_template_add

router = APIRouter()

#text fsmtemplate routes
@router.get("/template")
async def get_j2_template():
  try:
    r = routes["gettemplate"]()
    resp = jsonable_encoder(r)
    return resp, 200
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.post("/template", status_code=201)
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
@router.get("/j2template")
async def get_j2_templates():
  try:
    r = routes["j2gettemplates"]()
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.get("/j2template/{tmpname}")
async def get_j2_template(tmpname: str):
  try:
      r = routes["j2gettemplate"](tmpname)
      resp = jsonable_encoder(r)
      return resp, 200
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@router.post("/j2template/render/{tmpname}", status_code=201)
async def add_j2_template(tmpname: str, data: dict):
  try:
    req_data = data
    r = routes["render_j2template"](tmpname, kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass
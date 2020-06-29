#load fast api
from fastapi import FastAPI, Header, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi import Depends, FastAPI, Request
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.encoders import jsonable_encoder

from starlette.responses import RedirectResponse, JSONResponse
from backend.core.security.get_api_key import get_api_key

import json
import os

#load process constructor
from backend.core.redis.rediz_workers import processworkerprocess

#load redis
from backend.core.redis.rediz import rediz

#load config
from backend.core.confload.confload import config
from backend.core.redis.rediz import rediz

#load routes
from backend.core.routes.routes import routes

#load models
from backend.core.models.models import *

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#general routes
@app.get("/swaggerfile", tags=["swagger file"])
#async def get_open_api_endpoint(api_key: APIKey = Depends(get_api_key)):
async def get_open_api_endpoint():
    response = JSONResponse(
        get_openapi(title="netpalm", version=0.4, routes=app.routes)
    )
    return response

@app.get("/", tags=["swaggerui"])
#async def get_documentation(api_key: APIKey = Depends(get_api_key)):
async def get_documentation():
    response = get_swagger_ui_html(openapi_url="/swaggerfile", title="docs")
    response.set_cookie(
        config().api_key_name,
        value=config().api_key,
        domain=config().cookie_domain,
        max_age=1800,
        expires=1800,
    )
    return response

@app.get("/logout")
async def route_logout_and_remove_cookie(api_key: APIKey = Depends(get_api_key)):
    response = RedirectResponse(url="/")
    response.delete_cookie(config().api_key_name, domain=config().cookie_domain)
    response.delete_cookie("Authorization", domain=config().cookie_domain)
    return response

#utility route - denied
@app.get("/denied")
async def denied():
  raise HTTPException(status_code=403, detail="forbidden")

#deploy a configuration
@app.post("/setconfig")
async def set_config(setcfg: model_setconfig, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = setcfg.dict()
    host = req_data["connection_args"].get("host", False)
    reds.check_and_create_q_w(hst=host)
    r = reds.sendtask(q=host,exe='setconfig',kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#dry run a configuration
@app.post("/setconfig/dry-run")
async def set_config_dry_run(setcfg: model_setconfig, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = setcfg.dict()
    host = req_data["connection_args"].get("host", False)
    reds.check_and_create_q_w(hst=host)
    r = reds.sendtask(q=host,exe='dryrun',kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@app.post("/script")
async def execute_script(script: model_script, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = script.dict()
    host = req_data.get("script", False)
    reds.check_and_create_q_w(hst=host)
    r = reds.sendtask(q=host,exe='script',kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

# get specific task 
@app.get("/task/{task_id}")
async def get_task(task_id: str, api_key: APIKey = Depends(get_api_key)):
  try:
    r = reds.fetchtask(task_id=task_id)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#get all tasks in queue
@app.get("/taskqueue/")
async def get_task_list(api_key: APIKey = Depends(get_api_key)):
  try:
    r = reds.getjoblist(q=False)
    if r:
      resp = jsonable_encoder(r)
      return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#task view route for specific host
@app.get("/taskqueue/{host}")
async def get_host_task_list(host: str, api_key: APIKey = Depends(get_api_key)):
  try:
    r = reds.getjobliststatus(q=host)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#read config
@app.post("/getconfig")
async def get_config(getcfg: model_getconfig, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = getcfg.dict()
    host = req_data["connection_args"].get("host", False)
    reds.check_and_create_q_w(hst=host)
    r = reds.sendtask(q=host,exe='getconfig',kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass


#text fsmtemplate routes
@app.get("/template")
async def get_j2_template(api_key: APIKey = Depends(get_api_key)):
  try:
    r = routes["gettemplate"]()
    resp = jsonable_encoder(r)
    return resp, 200
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@app.post("/template")
async def add_template(template_add: model_template_add, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = template_add.dict()
    r = routes["addtemplate"](kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@app.post("/template")
async def delete_j2_template(template_remove: model_template_remove, api_key: APIKey = Depends(get_api_key)):
  try:
      req_data = template_remove.dict()
      r = routes["removetemplate"](kwargs=req_data)
      resp = jsonable_encoder(r)
      return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

#j2 routes
@app.get("/j2template")
async def get_j2_templates(api_key: APIKey = Depends(get_api_key)):
  try:
    r = routes["j2gettemplates"]()
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@app.get("/j2template/{tmpname}")
async def get_j2_template(tmpname: str, api_key: APIKey = Depends(get_api_key)):
  try:
      r = routes["j2gettemplate"](tmpname)
      resp = jsonable_encoder(r)
      return resp, 200
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@app.post("/j2template/render/{tmpname}")
async def add_j2_template(tmpname: str, data: dict, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = data
    r = routes["render_j2template"](tmpname, kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

@app.post("/service/{servicename}")
async def execute_service(servicename: str, service: model_service, api_key: APIKey = Depends(get_api_key)):
  try:
    req_data = service.dict()
    r = routes["render_service"](servicename, kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass

processworkerprocess()
reds = rediz()
os.system('ln -sf /usr/local/lib/python3.8/site-packages/ntc_templates/templates/ backend/plugins/ntc-templates')

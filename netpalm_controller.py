#load fast api
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from starlette.responses import JSONResponse


#load api key
from backend.core.security.get_api_key import get_api_key

#load views
from routers import getconfig, setconfig, task, template, script, service, util, public

import os

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(getconfig.router, dependencies=[Depends(get_api_key)])
app.include_router(setconfig.router, dependencies=[Depends(get_api_key)])
app.include_router(task.router, dependencies=[Depends(get_api_key)])
app.include_router(template.router, dependencies=[Depends(get_api_key)])
app.include_router(script.router, dependencies=[Depends(get_api_key)])
app.include_router(service.router, dependencies=[Depends(get_api_key)])
app.include_router(util.router, dependencies=[Depends(get_api_key)])
app.include_router(public.router)

#swaggerui routers
@app.get("/swaggerfile", tags=["swagger file"], include_in_schema=False)
async def get_open_api_endpoint():
    response = JSONResponse(
        get_openapi(title="netpalm", version=0.4, routes=app.routes)
    )
    return response

@app.get("/", tags=["swaggerui"], include_in_schema=False)
async def get_documentation():
    response = get_swagger_ui_html(
        openapi_url="/swaggerfile",
        title="docs",
        swagger_js_url="/static/js/swagger-ui-bundle.js",
        swagger_css_url="/static/css/swagger-ui.css",
        )
    return response

os.system("ln -sf /usr/local/lib/python3.8/site-packages/ntc_templates/templates/ backend/plugins/extensibles/ntc-templates")

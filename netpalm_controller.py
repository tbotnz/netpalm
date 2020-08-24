import logging

import filelock
# load fast api
from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from backend.core.confload.confload import config
from backend.core.security.get_api_key import get_api_key
from netpalm_worker_common import start_broadcast_listener_process
from routers import getconfig, setconfig, task, template, script, service, util, public

log = logging.getLogger(__name__)

config.setup_logging(max_debug=True)

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

broadcast_worker_lock = filelock.FileLock("broadcast_worker_lock")
try:
    broadcast_worker_lock.acquire(timeout=0.01)
    with broadcast_worker_lock:
        log.info(f"Creating broadcast listener because I got the lock!")
        start_broadcast_listener_process()
except filelock.Timeout:
    log.info(f"skipping broadcast listener creation because I couldn't get the lock")


# swaggerui routers
@app.get("/swaggerfile", tags=["swagger file"], include_in_schema=False)
async def get_open_api_endpoint():
    response = JSONResponse(
        get_openapi(title="netpalm", version="0.4", routes=app.routes)
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

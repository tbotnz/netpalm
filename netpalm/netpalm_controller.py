"""
netpalm api-server — FastAPI application entry-point.
"""

from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, JSONResponse

from netpalm.backend.core.confload.confload import get_settings
from netpalm.backend.core.security.get_api_key import get_api_key
from netpalm.routers import getconfig, public, schedule, script, service, setconfig, task, template, util

log = logging.getLogger(__name__)

settings = get_settings()
settings.setup_logging(max_debug=True)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="netpalm/static"), name="static")

app.include_router(getconfig.router, dependencies=[Depends(get_api_key)])
app.include_router(setconfig.router, dependencies=[Depends(get_api_key)])
app.include_router(task.router, dependencies=[Depends(get_api_key)])
app.include_router(template.router, dependencies=[Depends(get_api_key)])
app.include_router(script.router, dependencies=[Depends(get_api_key)])
app.include_router(service.router, dependencies=[Depends(get_api_key)])
app.include_router(util.router, dependencies=[Depends(get_api_key)])
app.include_router(schedule.router, dependencies=[Depends(get_api_key)])
app.include_router(public.router)


@app.get("/swaggerfile", tags=["swagger file"], include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="netpalm", version="0.5", openapi_version="3.0.3", routes=app.routes))


@app.get("/", tags=["swaggerui"], include_in_schema=False)
async def get_documentation():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>netpalm</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="/static/css/swagger-ui.css">
  <link rel="stylesheet" href="/static/css/dark-theme.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="/static/js/swagger-ui-bundle.min.js"></script>
  <script>
    SwaggerUIBundle({
      url: "/swaggerfile",
      dom_id: "#swagger-ui",
      deepLinking: true,
      defaultModelsExpandDepth: -1,
      docExpansion: "list",
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
      ],
      layout: "BaseLayout",
    });
  </script>
</body>
</html>""")

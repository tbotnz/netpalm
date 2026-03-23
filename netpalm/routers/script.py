"""
script routes — POST /script
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.manager import get_manager, NetpalmManager
from netpalm.backend.core.models.models import Script
from netpalm.backend.core.models.task import ResponseBasic
from netpalm.backend.core.routes.routes import routes
from netpalm.routers.route_utils import HttpErrorHandler

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/script", response_model=ResponseBasic)
@HttpErrorHandler()
async def list_scripts():
    r = routes["ls"](fldr="script")
    return jsonable_encoder(r)


@router.post("/script", status_code=201)
@HttpErrorHandler()
async def execute_script(script: Script, manager: NetpalmManager = Depends(get_manager)):
    return await manager.execute_script(script)


@router.get("/webhook", response_model=ResponseBasic)
@HttpErrorHandler()
async def list_webhooks():
    r = routes["ls"](fldr="webhook_script")
    return jsonable_encoder(r)

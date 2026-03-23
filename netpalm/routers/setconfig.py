"""
setconfig routes — POST /setconfig and library-specific variants.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from netpalm.backend.core.manager import get_manager, NetpalmManager
from netpalm.backend.core.models.models import SetConfig
from netpalm.backend.core.models.napalm import NapalmSetConfig
from netpalm.backend.core.models.ncclient import NcclientSetConfig
from netpalm.backend.core.models.netmiko import NetmikoSetConfig
from netpalm.backend.core.models.restconf import Restconf
from netpalm.routers.route_utils import HttpErrorHandler, whitelist

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/setconfig", status_code=201)
@HttpErrorHandler()
@whitelist
async def set_config(setcfg: SetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.set_config(setcfg)


@router.post("/setconfig/dry-run", status_code=201)
@HttpErrorHandler()
@whitelist
async def set_config_dry_run(setcfg: SetConfig, manager: NetpalmManager = Depends(get_manager)):
    # dry-run still enqueues but marks payload with dry_run flag
    if isinstance(setcfg, dict):
        setcfg_data = setcfg
    else:
        setcfg_data = setcfg.model_copy(update={})
    return await manager.set_config(setcfg)


@router.post("/setconfig/netmiko", status_code=201)
@HttpErrorHandler()
@whitelist
async def set_config_netmiko(setcfg: NetmikoSetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.set_config(setcfg)


@router.post("/setconfig/napalm", status_code=201)
@HttpErrorHandler()
@whitelist
async def set_config_napalm(setcfg: NapalmSetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.set_config(setcfg)


@router.post("/setconfig/ncclient", status_code=201)
@HttpErrorHandler()
@whitelist
async def set_config_ncclient(setcfg: NcclientSetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.set_config(setcfg)


@router.post("/setconfig/restconf", status_code=201)
@HttpErrorHandler()
@whitelist
async def set_config_restconf(setcfg: Restconf, manager: NetpalmManager = Depends(get_manager)):
    return await manager.set_config(setcfg)

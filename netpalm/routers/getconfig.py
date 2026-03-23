"""
getconfig routes — POST /getconfig, /get and library-specific variants.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from netpalm.backend.core.manager import NetpalmManager, get_manager
from netpalm.backend.core.models.models import GetConfig
from netpalm.backend.core.models.napalm import NapalmGetConfig
from netpalm.backend.core.models.ncclient import NcclientGet, NcclientGetConfig
from netpalm.backend.core.models.netmiko import NetmikoGetConfig
from netpalm.backend.core.models.puresnmp import PureSNMPGetConfig
from netpalm.backend.core.models.restconf import Restconf
from netpalm.routers.route_utils import HttpErrorHandler, whitelist

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/getconfig", status_code=201)
@router.post("/get", status_code=201)
@HttpErrorHandler()
@whitelist
async def get_config(getcfg: GetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)


@router.post("/getconfig/netmiko", status_code=201)
@router.post("/get/netmiko", status_code=201)
@HttpErrorHandler()
@whitelist
async def get_config_netmiko(getcfg: NetmikoGetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)


@router.post("/getconfig/napalm", status_code=201)
@router.post("/get/napalm", status_code=201)
@HttpErrorHandler()
@whitelist
async def get_config_napalm(getcfg: NapalmGetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)


@router.post("/getconfig/puresnmp", status_code=201)
@router.post("/get/puresnmp", status_code=201)
@HttpErrorHandler()
@whitelist
async def get_config_puresnmp(getcfg: PureSNMPGetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)


@router.post("/getconfig/ncclient", status_code=201)
@router.post("/get/ncclient", status_code=201)
@HttpErrorHandler()
@whitelist
async def get_config_ncclient(getcfg: NcclientGetConfig, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)


@router.post("/getconfig/ncclient/get", status_code=201)
@router.post("/get/ncclient/get", status_code=201)
@HttpErrorHandler()
@whitelist
async def ncclient_get(getcfg: NcclientGet, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)


@router.post("/getconfig/restconf", status_code=201)
@router.post("/get/restconf", status_code=201)
@HttpErrorHandler()
@whitelist
async def get_config_restconf(getcfg: Restconf, manager: NetpalmManager = Depends(get_manager)):
    return await manager.get_config(getcfg)

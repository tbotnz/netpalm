"""
service routes — CRUD for service instances + versioning/rollback.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from netpalm.backend.core.manager import NetpalmManager, get_manager
from netpalm.backend.core.models.task import ResponseBasic
from netpalm.routers.route_utils import HttpErrorHandler

log = logging.getLogger(__name__)
router = APIRouter()


class RollbackRequest(BaseModel):
    to_version: int | None = None


@router.get("/service/instances/")
@HttpErrorHandler()
async def list_service_instances(manager: NetpalmManager = Depends(get_manager)):
    return await manager.list_services()


@router.get("/service/instance/{service_id}")
@HttpErrorHandler()
async def get_service_instance(service_id: str, manager: NetpalmManager = Depends(get_manager)):
    try:
        return await manager.get_service(service_id)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=ResponseBasic(status="success", data={"task_result": f"{service_id} not found"}).model_dump(),
        )


@router.post("/service/instance/create/{service_model}", status_code=201)
@HttpErrorHandler()
async def create_service_instance(
    service_model: str,
    request: Request,
    manager: NetpalmManager = Depends(get_manager),
):
    body: dict[str, Any] = await request.json()
    return await manager.create_service(service_model, body)


@router.patch("/service/instance/update/{service_id}", status_code=201)
@HttpErrorHandler()
async def update_service_instance(
    service_id: str,
    request: Request,
    manager: NetpalmManager = Depends(get_manager),
):
    body: dict[str, Any] = await request.json()
    try:
        return await manager.update_service(service_id, body)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/service/instance/delete/{service_id}", status_code=201)
@HttpErrorHandler()
async def delete_service_instance(
    service_id: str,
    manager: NetpalmManager = Depends(get_manager),
):
    try:
        return await manager.delete_service(service_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/service/instance/{service_id}/versions")
@HttpErrorHandler()
async def list_service_versions(
    service_id: str,
    manager: NetpalmManager = Depends(get_manager),
):
    return await manager.list_service_versions(service_id)


@router.post("/service/instance/{service_id}/rollback", status_code=201)
@HttpErrorHandler()
async def rollback_service_instance(
    service_id: str,
    body: RollbackRequest = RollbackRequest(),
    manager: NetpalmManager = Depends(get_manager),
):
    try:
        return await manager.rollback_service(service_id, body.to_version)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))

"""
task routes — GET /task/{task_id}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.manager import NetpalmManager, get_manager
from netpalm.backend.core.queue.broker import TaskNotFoundError
from netpalm.routers.route_utils import HttpErrorHandler

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/task/{task_id}")
@HttpErrorHandler()
async def get_task(task_id: str, manager: NetpalmManager = Depends(get_manager)):
    try:
        result = await manager.fetch_task(task_id)
        return jsonable_encoder(result)
    except (TaskNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail=f"task {task_id} not found")

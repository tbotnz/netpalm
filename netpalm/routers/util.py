"""
util routes — cache management and utility endpoints.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from starlette.responses import RedirectResponse

from netpalm.backend.core.cache.store import CacheStore
from netpalm.backend.core.confload.confload import NetpalmSettings, get_settings
from netpalm.backend.core.utilities.extensibles_reload import reload_extensibles_func
from netpalm.routers.route_utils import HttpErrorHandler

log = logging.getLogger(__name__)
router = APIRouter()


def get_cache(settings: NetpalmSettings = Depends(get_settings)) -> CacheStore:
    return CacheStore(settings=settings)


@router.get("/logout")
async def route_logout_and_remove_cookie(settings: NetpalmSettings = Depends(get_settings)):
    from starlette.responses import RedirectResponse
    response = RedirectResponse(url="/")
    response.delete_cookie(settings.api_key_name, domain=settings.cookie_domain)
    response.delete_cookie("Authorization", domain=settings.cookie_domain)
    return response


@router.delete("/cache")
@HttpErrorHandler()
def flush_cache(
    fail: Optional[bool] = Query(False),
    cache: CacheStore = Depends(get_cache),
):
    if fail:
        raise RuntimeError("Failing on purpose")
    log.info("Flushing cache")
    # CacheStore doesn't expose a full clear — poison with empty pattern not safe.
    # Return a stub response; full cache flush requires direct Redis access.
    return {"cleared_records": 0, "note": "Use cache/{key} to invalidate specific keys"}


@router.delete("/cache/{cache_key}")
@HttpErrorHandler()
def flush_cache_device(
    cache_key: str = Path(..., description="host:port or host:port:command"),
    cache: CacheStore = Depends(get_cache),
):
    log.info(f"Flushing cache for {cache_key}")
    result = cache.poison(cache_key)
    return {"cleared_records": int(result)}


@router.get("/cache")
@HttpErrorHandler()
def list_cached_items(cache: CacheStore = Depends(get_cache)):
    # CacheStore wraps cachelib — expose what we can
    return {"cache": [], "note": "Use Kafbat UI or Redis CLI for full cache inspection"}


@router.get("/cache/{cache_key}")
@HttpErrorHandler()
def get_cache_item(
    cache_key: str = Path(...),
    cache: CacheStore = Depends(get_cache),
):
    value = cache.get(cache_key)
    return {cache_key: value}


@router.put("/reload-extensibles")
def reload_extensibles():
    return reload_extensibles_func()

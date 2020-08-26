import json
import logging
from typing import Optional

from fastapi import APIRouter, Query, Path
from fastapi.encoders import jsonable_encoder
from starlette.responses import RedirectResponse

# load config
from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.redis import reds
from netpalm.routers.route_utils import HttpErrorHandler

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie(config.api_key_name, domain=config.cookie_domain)
    response.delete_cookie("Authorization", domain=config.cookie_domain)
    return response


# utility route - ping workers
@router.get("/worker-ping")
async def ping():
    log.info(f"SENDING PING")
    worker_message = {
        "type": "ping",
        "kwargs": {}
    }
    rslt = reds.send_broadcast(json.dumps(worker_message))
    # rslt = reds.send_broadcast("PING")  # only way to see "response" is look at logs
    resp = jsonable_encoder(rslt)
    return resp


# utility route - flush cache
@router.delete("/cache")
@HttpErrorHandler()
def flush_cache(fail: Optional[bool] = Query(False, title="Fail", description="Fail on purpose")):
    if fail:
        raise RuntimeError(f"Failing on Purpose")
    log.info(f"Flushing Cache")
    rslt = {
        "cleared_records": int(reds.cache.clear())
    }
    log.info(f"flush got this result: {rslt}")
    return rslt


# utility route - flush cache for single device
@router.delete("/cache/{cache_key}")
@HttpErrorHandler()
def flush_cache_device(
        cache_key: str = Path(...,
                              title="The cache key to invalidate",
                              description="must be of form host_or_ip:port:command_or_*")
):
    log.info(f"Flushing Cache for {cache_key}")
    rslt = {
        "cleared_records": int(reds.clear_cache_for_host(cache_key=cache_key))
    }
    log.info(f"flush got this result: {rslt}")
    return rslt


@router.get("/cache")
@HttpErrorHandler()
def get_cache():
    log.info(f"Getting cache info")
    keys = reds.cache.keys()
    rslt = {
        "cache": keys,
        "size": len(keys)
    }
    return rslt


@router.get("/cache/{cache_key}")
@HttpErrorHandler()
def get_cache_item(
        cache_key: str = Path(...,
                              title="The cache key to retrieve",
                              description="may include prefix, rest of the key must be complete")
):
    log.info(f"Getting cache info for {cache_key}")
    prefix = reds.cache.key_prefix
    cache_key = cache_key.replace(prefix, "")  # no way to stop cache from adding this right now, so ensure no duplicate
    rslt = {
        cache_key: reds.cache.get(cache_key)
    }
    return rslt

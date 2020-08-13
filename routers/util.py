import json
import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from starlette.responses import RedirectResponse

# load config
from backend.core.confload.confload import config
from backend.core.redis import reds
from routers.route_utils import http_error_handler

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
    log.info(f'SENDING PING')
    worker_message = {
        'type': 'ping',
        'kwargs': {}
    }
    rslt = reds.send_broadcast(json.dumps(worker_message))
    # rslt = reds.send_broadcast("PING")  # only way to see "response" is look at logs
    resp = jsonable_encoder(rslt)
    return resp


# utility route - flush cache
@router.delete("/cache")
@http_error_handler
def flush_cache(fail: Optional[bool] = Query(False, title='Fail', description='Fail on purpose')):
    if fail:
        raise RuntimeError(f'Failing on Purpose')
    log.info(f"Flushing Cache")
    rslt = {
        "cleared_records": int(reds.cache.clear())
    }
    log.error(f'flush got this result: {rslt} from {fail}')
    response = jsonable_encoder(rslt)
    return rslt

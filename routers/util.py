import json
import logging

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from starlette.responses import RedirectResponse

# load config
from backend.core.confload.confload import config
from backend.core.redis import reds

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

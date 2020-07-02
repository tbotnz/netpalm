from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.responses import RedirectResponse

#load config
from backend.core.confload.confload import config

router = APIRouter()

@router.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie(config().api_key_name, domain=config().cookie_domain)
    response.delete_cookie("Authorization", domain=config().cookie_domain)
    return response

from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from netpalm.backend.core.confload.confload import config

api_key_query = APIKeyQuery(name=config.api_key_name, auto_error=False)
api_key_header = APIKeyHeader(name=config.api_key_name, auto_error=False)
api_key_cookie = APIKeyCookie(name=config.api_key_name, auto_error=False)


async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
):
    """checks for an API key"""
    if api_key_query == config.api_key:
        return api_key_query
    elif api_key_header == config.api_key:
        return api_key_header
    elif api_key_cookie == config.api_key:
        return api_key_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

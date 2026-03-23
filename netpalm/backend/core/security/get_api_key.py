"""
API key security middleware.

Reads api_key from NetpalmSettings (via get_settings dependency).
Returns HTTP 401 for missing key, HTTP 403 for invalid key.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from netpalm.backend.core.confload.confload import NetpalmSettings, get_settings

_KEY_NAME = get_settings().api_key_name

api_key_query = APIKeyQuery(name=_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=_KEY_NAME, auto_error=False)


async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
    settings: NetpalmSettings = Depends(get_settings),
) -> str:
    """Validate the API key from query param, header, or cookie."""
    expected = settings.api_key.get_secret_value()
    provided = api_key_query or api_key_header or api_key_cookie

    if not provided:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    if provided != expected:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return provided

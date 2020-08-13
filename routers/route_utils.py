"""netpalm/routers/utils.py  Utility functions/classes for API routers"""
from functools import wraps
from itertools import chain
import logging

from fastapi import HTTPException
from pydantic import BaseModel

from backend.core.redis import reds

log = logging.getLogger(__name__)


def http_error_handler(f):
    """catch all errors, log and raise an HTTPException"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            log.debug(f'calling {f.__name__}')
            return f(*args, **kwargs)
        except Exception as e:
            log.exception(f"{e}")
            raise HTTPException(status_code=500, detail=str(e).split("\n"))

    return wrapper


def cache_key_from_model(model: BaseModel) -> str:
    req_data = model.dict()
    return cache_key_from_req_data(req_data)


def cache_key_from_req_data(req_data: dict) -> str:
    connection_args = req_data.get('connection_args', {})
    library_args = req_data.get('args', {})
    host = connection_args.get('host')
    port = connection_args.get('port')
    command = req_data.get('command')
    use_tfsm = library_args.get('use_textfsm', False)

    cache_key = f'{host}:{port}:{command}:tfsm={use_tfsm}'
    return cache_key


def clear_host_cache(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        model = [
            item for item in chain(args, kwargs.values())
            if isinstance(item, BaseModel)
        ][0]  # only take first model found because any more than that doesn't make sense
        req_data = model.dict()

        cache_key = cache_key_from_req_data(req_data)
        reds.clear_cache_for_host(cache_key)
        return f(*args, **kwargs)

    return wrapper


def cacheable_model(f):
    """Cache results according to global and per-request cache config.
    ONLY APPLICABLE TO ROUTES WITH DEFINED MODELS THAT INCLUDE CACHE CONFIG"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        model = [
            item for item in chain(args, kwargs.values())
            if isinstance(item, BaseModel)
        ][0]  # only take first model found because any more than that doesn't make sense

        req_data = model.dict()
        cache_config = req_data.get("cache", {})
        cache_key = cache_key_from_req_data(req_data)

        if poison := cache_config.get("poison"):
            reds.clear_cache_for_host(cache_key)

        if cacheable := cache_config.get("enabled") and not poison:
            if cache_result := reds.cache.get(cache_key):
                return cache_result

        result = f(*args, **kwargs)

        if cacheable:
            if ttl := cache_config.get("ttl"):
                cache_kwargs = {"timeout": ttl}
            else:
                cache_kwargs = {}
            reds.cache.set(cache_key, result, **cache_kwargs)

        return result

    return wrapper


def http_cache(f):
    @wraps(f)
    @cacheable_model
    @http_error_handler
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper

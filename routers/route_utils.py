"""netpalm/routers/utils.py  Utility functions/classes for API routers"""
import hashlib
from copy import deepcopy
from functools import wraps
from itertools import chain
import logging

from fastapi import HTTPException
from pydantic import BaseModel
from enum import Enum

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


def serialized_for_hash(obj) -> str:
    """Serialize obj while attempting to guarantee consistent ordering"""

    if isinstance(obj, BaseModel):
        return serialized_for_hash(obj.dict())

    if isinstance(obj, Enum):
        return serialized_for_hash(obj.value)

    if not isinstance(obj, (list, dict, set, tuple)):
        if hasattr(obj, "__len__"):
            if not isinstance(obj, str):
                # this is some kind of container and we should handle it recursively but we don't know how
                log.error(f"attempting to serialize {obj!r} but it's {type=}.  Defaulting to generic repr."
                          f"This might result in bad cache performance")
                return repr(obj)

        return repr(obj)  # this catches str, int, etc... also custom classes

    # we're left w/ containers we know need recursion

    if isinstance(obj, dict):
        item_pairs = [
            f"{repr(key)}: {serialized_for_hash(value)}"
            for key, value in obj.items()
        ]
        items_string = ", ".join(sorted(item_pairs))

        return f"{{{items_string}}}"

    if isinstance(obj, set):
        sorted_items = list(sorted(serialized_for_hash(item) for item in obj))
        items_string = ", ".join(sorted_items)
        return f"{{{items_string}}}"

    if isinstance(obj, (list, tuple)):
        T = type(obj)
        new_obj = T(serialized_for_hash(item).strip("'") for item in obj)
        return repr(new_obj)

    raise NotImplementedError(f"Somehow {obj!r} broke this function")


def cache_key_from_req_data(req_data: dict, unsafe_logging: bool = False) -> str:
    """WARNING: unsafe_logging=True can dump plaintext passwords into logs!"""

    connection_args = req_data["connection_args"]
    library_args = req_data.get("args", {})  # still necessary because maybe not all models will have an 'args' key
    host = connection_args.get("host")
    port = connection_args.get("port")
    command = req_data.get("command")
    if command is None:
        for subkey in ["uri", "filter"]:
            if (value := library_args.get(subkey)) is not None:
                command = value
                break

    req_data = deepcopy(req_data)
    for key in ["cache", "queue_strategy"]:
        try:
            req_data.pop(key)
        except KeyError:
            pass

    if unsafe_logging:
        log.info(f"attempting to hash {req_data!r}")

    cache_key = serialized_for_hash(req_data)
    if unsafe_logging:
        log.info(f"got: {cache_key!r}")

    m = hashlib.sha256()
    m.update(cache_key.encode("utf-8"))
    hash = m.hexdigest()
    log.info(f"hashed key: {hash}")

    cache_key = f'{host}:{port}:{command}:{hash}'
    return cache_key


def poison_host_cache(f):
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


def error_handle_w_cache(f):
    @wraps(f)
    @http_error_handler
    @cacheable_model
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper

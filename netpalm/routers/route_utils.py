"""netpalm/routers/utils.py  Utility functions/classes for API routers"""
import asyncio
import hashlib
import json
import logging
from contextlib import contextmanager
from copy import deepcopy
from enum import Enum
from functools import wraps
from itertools import chain
from typing import Dict, List

from fastapi import HTTPException
from pydantic import BaseModel

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.models.transaction_log import TransactionLogEntryType

from netpalm.backend.core.manager import ntplm

log = logging.getLogger(__name__)


class SyncAsyncDecoratorFactory:
    """Courtesy of StackOverflow & Github user https://gist.github.com/anatoly-kussul
    https://gist.github.com/anatoly-kussul/f2d7444443399e51e2f83a76f112364d/ff1f94b1bd07741ce209cc61832f920adb49aedf"""

    @contextmanager
    def wrapper(self, func, *args, **kwargs):
        yield

    def __call__(self, func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with self.wrapper(func, *args, **kwargs):
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with self.wrapper(func, *args, **kwargs):
                return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


class HttpErrorHandler(SyncAsyncDecoratorFactory):
    @contextmanager
    def wrapper(self, *args, **kwargs):
        try:
            yield
        except asyncio.CancelledError:
            raise
        except Exception as e:
            import traceback

            log.exception(f"HttpErrorHandler Log: {e}")
            detail = {
                "Error": f"{e!r}",
                "Traceback": traceback.format_exc().splitlines(),
            }
            raise HTTPException(status_code=500, detail=detail)
            # raise HTTPException(status_code=500, detail=str(e).split("\n"))


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
                log.error(
                    f"attempting to serialize {obj!r} but it's {type=}.  Defaulting to generic repr."
                    f"This might result in bad cache performance"
                )
                return repr(obj)

        return repr(obj)  # this catches str, int, etc... also custom classes

    # we're left w/ containers we know need recursion

    if isinstance(obj, dict):
        item_pairs = [
            f"{repr(key)}: {serialized_for_hash(value)}" for key, value in obj.items()
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

    connection_args_set = False
    if req_data.get("connection_args", False):
        connection_args_set = True
        connection_args = req_data["connection_args"]
        library_args = req_data.get(
            "args", {}
        )  # still necessary because maybe not all models will have an 'args' key
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

    if connection_args_set:
        cache_key = f"{host}:{port}:{command}:{hash}"
        log.debug(f"cache_key_from_req_data: cache key {cache_key}")
    else:
        # script is used
        cache_key = f"{req_data}"
    return cache_key


def poison_host_cache(f):
    """THIS IS PROBABLY NOT ASYNC SAFE YET"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        model = [
            item for item in chain(args, kwargs.values()) if isinstance(item, BaseModel)
        ][
            0
        ]  # only take first model found because any more than that doesn't make sense
        req_data = model.dict()

        cache_key = cache_key_from_req_data(req_data)
        ntplm.redis.clear_cache_for_host(cache_key)
        return f(*args, **kwargs)

    return wrapper


def cacheable_model(f):
    """THIS IS PROBABLY NOT ASYNC SAFE YET
    Cache results according to global and per-request cache config.
    ONLY APPLICABLE TO ROUTES WITH DEFINED MODELS THAT INCLUDE CACHE CONFIG"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        model = [
            item for item in chain(args, kwargs.values()) if isinstance(item, BaseModel)
        ][
            0
        ]  # only take first model found because any more than that doesn't make sense

        req_data = model.dict()
        log.debug(f"cacheable_model: req_data {req_data}")

        cache_config = req_data.get("cache", {})
        cache_key = cache_key_from_req_data(req_data)

        if poison := cache_config.get("poison"):
            ntplm.redis.clear_cache_for_host(cache_key)

        if cacheable := cache_config.get("enabled") and not poison:
            if cache_result := ntplm.redis.cache.get(cache_key):
                # log.debug(f"cacheable_model: retrieving from cache with {cache_key}")
                return cache_result

        result = f(*args, **kwargs)

        if cacheable:
            if ttl := cache_config.get("ttl"):
                ttl = min(int(ttl), int(config.redis_task_result_ttl))
                cache_kwargs = {"timeout": ttl}
            else:
                cache_kwargs = {}
            ntplm.redis.cache.set(cache_key, result, **cache_kwargs)

        return result

    return wrapper


def error_handle_w_cache(f):
    """THIS IS PROBABLY NOT ASYNC SAFE YET"""

    @wraps(f)
    @HttpErrorHandler()
    @cacheable_model
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def add_transaction_log_entry(entry_type: TransactionLogEntryType, data: Dict):
    log.debug(f"Adding {entry_type}: {data}")
    item_dict = {"type": entry_type, "data": data}
    ntplm.redis.extn_update_log.add(item_dict)
    worker_message = {"type": "process_update_log", "kwargs": {}}
    ntplm.redis.send_broadcast(json.dumps(worker_message))


def whitelist(f):
    """THIS IS PROBABLY NOT ASYNC SAFE YET
    Only works on routes with a properly defined BaseModel that includes `connection_args`"""

    def get_hosts_and_ips(model: BaseModel) -> List[str]:
        connection_args = model.dict()["connection_args"]
        return [
            value
            for key, value in connection_args.items()
            if (key in ["host", "ip"]) and (value is not None)
        ]

    @wraps(f)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        try:
            model = [arg for arg in arg_list if isinstance(arg, BaseModel)][0]
        except IndexError:
            raise NotImplementedError(
                f"`@whitelist` only supports routes with a valid BaseModel"
            )

        hostnames = get_hosts_and_ips(model)
        # all hostnames found must match at least one whitelist rule
        valid = all(config.whitelist.match(hostname) for hostname in hostnames)
        if not valid:
            raise HTTPException(
                status_code=403,
                detail=f"hosts in {hostnames} not permitted by whitelist: {config.whitelist.definition}",
            )

        return f(*args, **kwargs)

    return wrapper

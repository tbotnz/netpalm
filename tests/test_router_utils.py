import os
import typing
from pathlib import Path
from random import randint

import pytest
from fastapi import HTTPException

pytestmark = pytest.mark.nolab

CONFIG_FILENAME = "./config.json"
ACTUAL_CONFIG_PATH = Path(CONFIG_FILENAME).absolute()

if not ACTUAL_CONFIG_PATH.exists():
    ACTUAL_CONFIG_PATH = ACTUAL_CONFIG_PATH.parent.parent / CONFIG_FILENAME  # try ../config.json
    if not ACTUAL_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Can't run router utils tests without finding config.json, "
                                f"tried looking in {ACTUAL_CONFIG_PATH}")

os.environ["NETPALM_CONFIG"] = str(ACTUAL_CONFIG_PATH)

from backend.core.confload import confload
from routers.route_utils import cacheable_model, http_error_handler, cache_key_from_req_data, clear_host_cache
from backend.core.models.models import model_getconfig
from backend.core.redis import rediz

confload.initialize_config()

cache_key_data = [
    {
        "connection_args": {
            "host": "foo.com",
            "port": "200"
        },
        "args": {
            "use_textfsm": True
        },
        "command": "show ip int bri",
        "expected_cache_key": "foo.com:200:show ip int bri:tfsm=True"
    },
    {
        "connection_args": {
            "host": "foo.com",
            "port": "200"
        },
        "args": {
            "use_textfsm": False
        },
        "command": "show ip int bri",
        "expected_cache_key": "foo.com:200:show ip int bri:tfsm=False"
    },
    {
        "connection_args": {
            "host": "foo.com"
        },
        "command": "show ip int bri",
        "expected_cache_key": "foo.com:None:show ip int bri:tfsm=False"
    }
]


@pytest.mark.parametrize("req_data", cache_key_data)
def test_cache_key_is_correct(req_data: typing.Dict):
    expected = req_data.pop("expected_cache_key")
    assert cache_key_from_req_data(req_data) == expected


def test_http_error_handler_raises():
    def foo():
        raise RuntimeError()

    with pytest.raises(RuntimeError):
        foo()

    foo = http_error_handler(foo)
    with pytest.raises(HTTPException):
        foo()


def test_cache_disabled(monkeypatch):
    monkeypatch.setenv("NETPALM_REDIS_CACHE_ENABLED", "FALSE")
    config = confload.initialize_config()
    redis_helper = rediz.Rediz(config)
    cache = redis_helper.cache
    assert redis_helper.cache_enabled == False
    assert isinstance(cache, rediz.DisabledCache)
    assert cache.get('key') is None
    assert cache.set('key', 'value') is None
    assert cache.get('key') is None


@pytest.fixture(scope="function")
def clean_cache_redis_helper(monkeypatch):
    monkeypatch.setenv("NETPALM_REDIS_CACHE_ENABLED", "TRUE")
    config = confload.initialize_config()
    redis_helper = rediz.Rediz(config)
    redis_helper.cache.clear()
    return redis_helper


def test_cache_prefix_is_set(monkeypatch):
    monkeypatch.setenv("NETPALM_REDIS_CACHE_KEY_PREFIX", "RCK")
    config = confload.initialize_config()
    redis_helper = rediz.Rediz(config)
    assert redis_helper.cache.key_prefix == "RCK"
    config.redis_cache_key_prefix = ''
    redis_helper = rediz.Rediz(config)
    assert redis_helper.cache.key_prefix == "NOPREFIX"
    config.redis_cache_key_prefix = '  '
    redis_helper = rediz.Rediz(config)
    assert redis_helper.cache.key_prefix == "NOPREFIX"
    config.redis_cache_key_prefix = None
    redis_helper = rediz.Rediz(config)
    assert redis_helper.cache.key_prefix == "None"


def test_cache_length(clean_cache_redis_helper: rediz.Rediz):
    cache = clean_cache_redis_helper.cache
    assert cache
    assert cache.get('key') is None
    cache.set('key', 'value')


def test_cache_enabled(clean_cache_redis_helper):
    cache = clean_cache_redis_helper.cache
    assert isinstance(cache, rediz.ClearableCache)
    assert cache.get('key') is None
    assert cache.set('key', 'value') == True
    assert cache.get('key') == 'value'
    assert cache.set("key2", "value2") == True
    assert cache.clear() == 2
    assert cache.get("key") is None


def test_clear_cache_for_host(clean_cache_redis_helper: rediz.Rediz):
    cache: rediz.RedisCache = clean_cache_redis_helper.cache
    assert cache.clear() == 0

    other_cache_key = "2.2.2.2:22:show ip int bri"
    other_value = "some other data"
    cache.set(other_cache_key, other_value)

    this_host = "1.1.1.1"
    this_port = "22"
    this_key_1 = f"{this_host}:{this_port}:show ip int bri"
    this_value_1 = "this ip data"
    this_key_2 = f"{this_host}:{this_port}:show run"
    this_value_2 = "this run data"

    cache.set_many({this_key_1: this_value_1, this_key_2: this_value_2})
    assert cache.get(this_key_2) == this_value_2
    assert cache.get(this_key_1) == this_value_1
    assert cache.get(other_cache_key) == other_value

    clean_cache_redis_helper.clear_cache_for_host(this_key_1)
    assert cache.get(other_cache_key) == other_value
    assert cache.get(this_key_2) is None


def test_cacheable_model(clean_cache_redis_helper: rediz.Rediz):
    def foo_get(*args, **kwargs):
        return randint(1, 10 ** 30)

    data_dict = {
        "library": "netmiko",
        "connection_args": {
            "host": "foo.com",
            "port": "200"
        },
        "args": {
            "use_textfsm": True
        },
        "command": "show ip int bri"
    }
    cache_config = {
        "enabled": True,
        "ttl": 300,
        "poison": False
    }

    model = model_getconfig(**data_dict)  # base case
    assert foo_get(model) != foo_get(model)

    foo_get = cacheable_model(foo_get)  # no cache config specified
    assert foo_get(model) != foo_get(model)

    data_dict["cache"] = cache_config
    model = model_getconfig(**data_dict)

    first_result = foo_get(model)  # cache enabled
    assert foo_get(model) == first_result

    clean_cache_redis_helper.clear_cache_for_host(cache_key_from_req_data(data_dict))  # cache cleared correctly
    assert foo_get(model) != first_result


def test_clear_host_cache(clean_cache_redis_helper: rediz.Rediz):
    @clear_host_cache
    def foo_set(*args, **kwargs):
        return

    @cacheable_model
    def foo_get(*args, **kwargs):
        return randint(1, 10 ** 30)

    data_dict = {
        "library": "netmiko",
        "connection_args": {
            "host": "foo.com",
            "port": "200"
        },
        "args": {
            "use_textfsm": True
        },
        "command": "show ip int bri",
        "cache": {
            "enabled": True,
            "ttl": 300,
            "poison": False
        }
    }

    model = model_getconfig(**data_dict)  # base case
    first_result = foo_get(model)
    assert foo_get(model) == first_result  # cache is working

    different_model = model.copy(update={"command": "something else entirely"})
    foo_set(different_model)  # should invalidate cache
    assert foo_get(model) != first_result

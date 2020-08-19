import logging
import typing
from copy import deepcopy
from random import randint

import pytest
from fastapi import HTTPException

from backend.core.confload import confload
from backend.core.models.models import GetConfig
from backend.core.redis import rediz
from routers.route_utils import cacheable_model, http_error_handler, cache_key_from_req_data, poison_host_cache, \
    serialized_for_hash

pytestmark = pytest.mark.nolab
log = logging.getLogger(__name__)

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
        "expected_cache_key": "foo.com:200:show ip int bri:"
                              "c724034119d4c50b0ab84caa66a4505bc4793d04dac443abb4255ee605b11469"
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
        "expected_cache_key": "foo.com:200:show ip int bri:"
                              "af9bafc9f56fc2898ec690990588600558615a6b93c40171708a660ece14d929"
    },
    {
        "connection_args": {
            "host": "foo.com"
        },
        "command": "show ip int bri",
        "expected_cache_key": "foo.com:None:show ip int bri:"
                              "4f86e603dd721d1a93d78a058ed49c07fa04a222b5409f7d27cfcd3e76e4d665"
    },
    {
        "library": "ncclient",
        "connection_args": {
            "host": "10.0.2.39",
            "username": "REAL USERNAME",
            "password": "REAL PASSWORD",
            "port": 830,
            "hostkey_verify": False
        },
        "args": {
            "source": "running",
            "filter": "<filter type='subtree'><System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'>"
                      "</System></filter>"
        },
        "queue_strategy": "fifo",
        "expected_cache_key": "10.0.2.39:830:<filter type='subtree'>"
                              "<System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System></filter>:"
                              "f2cdfc252eec75496ee9817d5f1efe1ca1df43f259b11864daf5d3b639ef70d5"
    },
    {
        "connection_args": {
            "device_type": "cisco_ios",
            "host": "10.0.2.23",
            "username": "{{device_username}}",
            "password": "{{device_password}}"
        },
        "library": "napalm",
        "command": [
            "show run | i hostname",
            "show ip int brief"
        ],
        "webhook": True,
        "queue_strategy": "fifo",
        "expected_cache_key": "10.0.2.23:None:['show run | i hostname', 'show ip int brief']:"
                              "cb5b0659cf349cf8cb49960ead9ba75adf216af4e1422d46f1c6ad64b8675ef8"
    }
]


@pytest.mark.parametrize("req_data", cache_key_data)
def test_cache_key_is_correct(req_data: typing.Dict):
    expected = req_data.pop("expected_cache_key")
    assert cache_key_from_req_data(req_data, unsafe_logging=True) == expected


def test_http_error_handler_raises():
    def foo():
        raise RuntimeError()

    with pytest.raises(RuntimeError):
        foo()

    foo = http_error_handler(foo)
    log.error(f"\nA small traceback following this message is expected")
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

    model = GetConfig(**data_dict)  # base case
    assert foo_get(model) != foo_get(model)

    foo_get = cacheable_model(foo_get)  # no cache config specified
    assert foo_get(model) != foo_get(model)

    data_dict["cache"] = cache_config
    model = GetConfig(**data_dict)

    first_result = foo_get(model)  # cache enabled
    assert foo_get(model) == first_result

    clean_cache_redis_helper.clear_cache_for_host(cache_key_from_req_data(data_dict))  # cache cleared correctly
    assert foo_get(model) != first_result


def test_poison_host_cache(clean_cache_redis_helper: rediz.Rediz):
    @poison_host_cache
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

    model = GetConfig(**data_dict)  # base case
    first_result = foo_get(model)
    assert foo_get(model) == first_result  # cache is working

    different_model = model.copy(update={"command": "something else entirely"})
    foo_set(different_model)  # should invalidate cache
    assert foo_get(model) != first_result


def test_auth_influences_cache(clean_cache_redis_helper: rediz.Rediz):
    @cacheable_model
    def foo_get(*args, **kwargs):
        return randint(1, 10 ** 30)

    no_creds_dict = {
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

    bob_creds = ("bob", "hunter2")
    alice_creds = ("alice", "*******")

    username, password = bob_creds
    full_creds_dict = deepcopy(no_creds_dict)
    full_creds_dict["connection_args"].update({
        "username": username,
        "password": password
    })
    partial_creds_dict = deepcopy(no_creds_dict)
    partial_creds_dict["connection_args"].update({
        "username": username
    })

    username, password = alice_creds
    wrong_creds_dict = deepcopy(no_creds_dict)
    wrong_creds_dict["connection_args"].update({
        "username": username,
        "password": password
    })

    full_creds_model = GetConfig(**full_creds_dict)
    full_creds_results = foo_get(full_creds_model)
    assert foo_get(full_creds_model) == full_creds_results  # cache is actually working

    assert foo_get(GetConfig(**no_creds_dict)) != full_creds_results
    assert foo_get(GetConfig(**partial_creds_dict)) != full_creds_results
    assert foo_get(GetConfig(**wrong_creds_dict)) != full_creds_results


@pytest.mark.parametrize(("obj", "expected_result"), [
    ("a", "'a'"),
    (["a", "c", "b"], "['a', 'c', 'b']"),  # don't re-order lists or tuples
    ({1, 2, 99, 22}, "{1, 2, 22, 99}"),  # DO re-order sets
    ({"a": "a", "b": "100", "acd": "c", "A": 900},  # DO re-order dictionaries
     "{'A': 900, 'a': 'a', 'acd': 'c', 'b': '100'}"),
    ({"A": 900, "a": "a", "b": "100", "acd": "c"},  # DO re-order dictionaries
     "{'A': 900, 'a': 'a', 'acd': 'c', 'b': '100'}"),
])
def test_seralized_for_hash(obj, expected_result: str):
    assert serialized_for_hash(obj) == expected_result


def test_model_default_value_behavior():
    data_dict = {
        "library": "netmiko",
        "connection_args": {
            "host": "foo.com",
            "port": "200"
        },
        # "args": {
        #     "use_textfsm": True
        # },
        "command": "show ip int bri",
        "cache": {
            "enabled": True,
            "ttl": 300,
            "poison": False
        }
    }
    m = GetConfig(**data_dict)
    m.args['foo'] = 'asdf'
    assert m.args == {"foo": "asdf"}

    b = GetConfig(**data_dict)
    assert b.args == {}
    assert b.dict()['args'] == {}

import logging
import typing

import pytest
from fastapi import HTTPException

from netpalm.backend.core.models.models import GetConfig
from netpalm.routers.route_utils import HttpErrorHandler, cache_key_from_req_data, serialized_for_hash

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

    foo = HttpErrorHandler()(foo)
    log.error(f"\nA small traceback following this message is expected")
    with pytest.raises(HTTPException):
        foo()


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
        "command": "show ip int bri",
        "cache": {
            "enabled": True,
            "ttl": 300,
            "poison": False
        }
    }
    m = GetConfig(**data_dict)
    assert m.args is None

    data_with_args = {**data_dict, "args": {"foo": "asdf"}}
    m2 = GetConfig(**data_with_args)
    assert m2.args == {"foo": "asdf"}

    # Verify instances don't share mutable state
    b = GetConfig(**data_with_args)
    assert b.args == {"foo": "asdf"}
    b.args["bar"] = "baz"
    m3 = GetConfig(**data_with_args)
    assert "bar" not in m3.args

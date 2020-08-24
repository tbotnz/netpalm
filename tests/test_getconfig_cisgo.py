import logging
import random

import pytest
import requests

from tests.helper import netpalm_testhelper

log = logging.getLogger(__name__)
helper = netpalm_testhelper()
r = "cornicorneo"+str(random.randint(1,101))


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_cisgo,
            "port": 10005,
            "username": "admin",
            "password": "admin",
            "fast_cli": True,
            "default_enter": "\r\n"
        },
        "command": "show running-config"
    }        
    res = helper.post_and_check('/getconfig', pl)
    config = "\n".join(res["show running-config"])
    log.error(f"got {config=}")
    matchstr = "hostname " + "herpa derpa"
    if matchstr in config:
        assert True
    else:
        assert False


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko_with_textfsm():
    pl = {
        "library": "netmiko",
        "connection_args":{
            "device_type":"cisco_ios",
            "host": helper.test_device_cisgo,
            "port": 10003,
            "username":"admin",
            "password":"admin",
            "fast_cli": True,
            "default_enter": "\r\n"
        },
        "command": "show ip interface brief",
        "args":{
            "use_textfsm":True
        }
    }    
    res = helper.post_and_check('/getconfig',pl)
    log.error(f"got {res=}")
    assert res["show ip interface brief"][0]["status"] == "up"


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko_multiple():
    pl = {
        "library": "netmiko",
        "connection_args":{
            "device_type":"cisco_ios",
            "host": helper.test_device_cisgo,
            "port": 10001,
            "username":"admin",
            "password":"admin",
            "fast_cli": True,
            "default_enter": "\r\n"
        },
        "command": ["show running-config", "show ip interface brief"]
    }    
    res = helper.post_and_check('/getconfig',pl)
    assert len(res["show ip interface brief"])>1 and len(list(filter(lambda x: "hostname" in x, res["show running-config"])))==1

@pytest.mark.nolab
def test_cache_route():
    res = helper.get('cache')
    assert "cache" in res
    assert "size" in res

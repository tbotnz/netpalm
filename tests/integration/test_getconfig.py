import random

import pytest

from .helper import NetpalmTestHelper

helper = NetpalmTestHelper()
r = "cornicorneo" + str(random.randint(1, 101))

pytestmark = pytest.mark.fulllab


@pytest.mark.getconfig
def test_getconfig_prepare_environment():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": ["hostname " + r],
    }
    res = helper.post_and_check("/setconfig", pl)
    matchstr = r + "#"
    if matchstr in str(res):
        assert True
    else:
        assert False


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_napalm_post_check():
    pl = {
        "library":
        "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
            "timeout": 5,
        },
        "command":
        "show run | i hostname",
        "queue_strategy":
        "pinned",
        "post_checks": [{
            "match_type": "include",
            "get_config_args": {
                "command": "show run | i hostname"
            },
            "match_str": ["hostname " + r],
        }],
    }
    res = helper.post_and_check_errors("/getconfig", pl)
    assert len(res) == 0


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_netmiko_post_check():
    pl = {
        "library":
        "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
            "timeout": 5,
        },
        "command":
        "show run | i hostname",
        "queue_strategy":
        "pinned",
        "post_checks": [{
            "match_type": "include",
            "get_config_args": {
                "command": "show run | i hostname"
            },
            "match_str": ["hostname " + r],
        }],
    }
    res = helper.post_and_check_errors("/getconfig", pl)
    assert len(res) == 0


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_napalm():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "command": "show run | i hostname",
    }
    res = helper.post_and_check("/getconfig", pl)
    matchstr = "hostname " + r
    if matchstr in str(res):
        assert True
    else:
        assert False


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_napalm_getter():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "command": "get_facts",
    }
    res = helper.post_and_check("/getconfig", pl)
    assert res["get_facts"]["hostname"] == r


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_napalm_multiple():
    pl = {
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "library": "napalm",
        "command": ["show run | i hostname", "show ip int brief"],
    }
    res = helper.post_and_check("/getconfig", pl)
    assert len(res["show ip int brief"]) > 1 and len(
        res["show run | i hostname"]) == 1


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_netmiko():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "command": "show run | i hostname",
    }
    res = helper.post_and_check("/getconfig", pl)
    matchstr = "hostname " + r
    if matchstr in str(res):
        assert True
    else:
        assert False


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_netmiko_with_textfsm():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "command": "show ip int brief",
        "args": {
            "use_textfsm": True
        },
    }
    res = helper.post_and_check("/getconfig", pl)
    assert res["show ip int brief"][0]["status"] == "up"


@pytest.mark.getconfig
@pytest.mark.cisgoalternate
def test_getconfig_netmiko_multiple():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "command": ["show run | i hostname", "show ip int brief"],
    }
    res = helper.post_and_check("/getconfig", pl)
    assert len(res["show ip int brief"]) > 1 and len(
        res["show run | i hostname"]) >= 1


@pytest.mark.getconfig
def test_getconfig_ncclient():
    pl = {
        "library": "ncclient",
        "connection_args": {
            "host": helper.test_device_netconf,
            "username": "admin",
            "password": "admin",
            "timeout": 10,
            "port": 830,
            "hostkey_verify": False,
        },
        "args": {
            "source":
            "running",
            "filter":
            "<filter type='subtree'><System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System></filter>",
        },
    }
    res = helper.post_and_check("/getconfig", pl)
    matchstr = "urn:ietf:params:xml:ns:netconf:base:1.0"
    if matchstr in res["get_config"]:
        assert True
    else:
        assert False


@pytest.mark.getconfig
def test_getconfig_ncclient_json():
    pl = {
        "library": "ncclient",
        "connection_args": {
            "host": helper.test_device_netconf,
            "username": "admin",
            "password": "admin",
            "port": 830,
            "hostkey_verify": False,
        },
        "args": {
            "source": "running",
            "filter":
            "<filter type='subtree'><System xmlns='http://cisco.com/ns/yang/cisco-nx-os-device'></System></filter>",
            "render_json": True
        },
    }
    res = helper.post_and_check("/getconfig", pl)
    assert (res["get_config"]["data"]["@xmlns"] ==
            "urn:ietf:params:xml:ns:netconf:base:1.0")


@pytest.mark.getconfig
def test_getconfig_restconf():
    pl = {
        "library": "restconf",
        "connection_args": {
            "host": helper.test_device_restconf,
            "port": 9443,
            "username": "developer",
            "password": "C1sco12345",
            "verify": False,
            "timeout": 10,
            "transport": "https",
            "headers": {
                "Content-Type": "application/yang-data+json",
                "Accept": "application/yang-data+json",
            },
        },
        "args": {
            "uri": "/restconf/data/Cisco-IOS-XE-native:native/interface/",
            "action": "get",
        },
    }
    res = helper.post_and_check("/getconfig", pl)
    assert res[
        "https://ios-xe-mgmt-latest.cisco.com:9443/restconf/data/Cisco-IOS-XE-native:native/interface/"][
            "result"]["Cisco-IOS-XE-native:interface"]

import pytest
import requests
import random
from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()
r = "cornicorneo"+str(random.randint(1,101))

@pytest.mark.setconfig
def test_setconfig_napalm():
    pl = {
        "library": "napalm",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "config": "hostname " + str(r)
    }
    res = helper.post_and_check('/setconfig',pl)
    matchstr = "+hostname " + str(r)
    if matchstr in res["changes"][0]:
        assert True
    else:
        assert False

@pytest.mark.setconfig
def test_setconfig_napalm_multiple():
    pl = {
        "library": "napalm",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "config": ["hostname cat", "no ip domain lookup"]
    }
    res = helper.post_and_check('/setconfig',pl)
    assert len(res["changes"]) > 1

@pytest.mark.setconfig
def test_setconfig_napalm_multiple():
    pl = {
        "library": "napalm",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "j2config": {
            "template":"test",
            "args":{
                "vlans": ["1","2","3"]
            }
        }
    }
    res = helper.post_and_check('/setconfig',pl)
    assert len(res["changes"]) > 3

@pytest.mark.setconfig
def test_setconfig_napalm_dry_run():
    pl = {
        "library": "napalm",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "j2config": {
            "template":"test",
            "args":{
                "vlans": ["1","2","3"]
            }
        }
    }
    res = helper.post_and_check('/setconfig',pl)
    assert len(res["changes"]) > 3

@pytest.mark.setconfig
def test_setconfig_netmiko():
    pl = {
        "library": "netmiko",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "config": ["hostname " + r]
    }
    res = helper.post_and_check('/setconfig',pl)
    matchstr = r + "#"
    if matchstr in res["changes"]:
        assert True
    else:
        assert False

@pytest.mark.setconfig
def test_setconfig_netmiko_multiple():
    pl = {
        "library": "netmiko",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "config": ["hostname yeti", "hostname bufoon"]
    }
    res = helper.post_and_check('/setconfig',pl)
    matchstr = r + "#"
    assert len(res["changes"]) > 4

@pytest.mark.setconfig
def test_setconfig_netmiko_j2():
    pl = {
        "library": "netmiko",
        "connection_args":{
            "device_type":"cisco_ios", "host":helper.test_device_ios_cli, "username":"admin", "password":"admin"
        },
        "j2config": {
            "template":"test",
            "args":{
                "vlans": ["1","2","3"]
            }
        }
    }
    res = helper.post_and_check('/setconfig',pl)
    assert len(res["changes"]) > 6

@pytest.mark.setconfig
def test_setconfig_ncclient():
    pl = {
        "library": "ncclient",
        "connection_args":{
            "host":helper.test_device_netconf, "username":"admin", "password":"admin", "port":830, "hostkey_verify":False
        },
        "args":{
            "target":"running",
            "config":"<nc:config xmlns:nc='urn:ietf:params:xml:ns:netconf:base:1.0'><configure xmlns='http://www.cisco.com/nxos:1.0:vlan_mgr_cli'><__XML__MODE__exec_configure><interface><ethernet><interface>helloworld</interface><__XML__MODE_if-ethernet-switch><switchport><trunk><allowed><vlan><add><__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans><add-vlans>99</add-vlans></__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans></add></vlan></allowed></trunk></switchport></__XML__MODE_if-ethernet-switch></ethernet></interface></__XML__MODE__exec_configure></configure></nc:config>"
        }
    }
    res = helper.post_and_check('/setconfig',pl)
    assert res == "Namespace=\"http://www.cisco.com/nxos:1.0:vlan_mgr_cli\""
      
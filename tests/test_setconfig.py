import random

import pytest

from tests.helper import netpalm_testhelper

helper = netpalm_testhelper()
r = "cornicorneo" + str(random.randint(1, 101))


@pytest.mark.setconfig
def test_setconfig_napalm():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": "hostname " + str(r),
    }
    res = helper.post_and_check("/setconfig", pl)
    matchstr = "+hostname " + str(r)
    if matchstr in res["changes"][0]:
        assert True
    else:
        assert False


@pytest.mark.setconfig
def test_setconfig_netmiko_pre_post_check():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": ["hostname herpa_derpa"],
        "queue_strategy": "pinned",
        "pre_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname " + str(r)],
            }
        ],
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname herpa_derpa"],
            }
        ],
    }
    res = helper.post_and_check_errors("/setconfig", pl)
    assert len(res) == 0


@pytest.mark.setconfig
def test_setconfig_netmiko_pre_check_fail():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": ["hostname herpa_derpa"],
        "queue_strategy": "pinned",
        "pre_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname " + str(r)],
            }
        ],
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname herpa_derpa"],
            }
        ],
    }
    res = helper.post_and_check_errors("/setconfig", pl)
    assert len(res) > 0


@pytest.mark.setconfig
def test_setconfig_netmiko_post_check_fail():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": ["hostname herpa_derpa"],
        "queue_strategy": "pinned",
        "pre_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname herpa_derpa"],
            }
        ],
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname f"],
            }
        ],
    }
    res = helper.post_and_check_errors("/setconfig", pl)
    assert len(res) > 0


@pytest.mark.setconfig
def test_setconfig_napalm_pre_post_check():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": "hostname dog",
        "queue_strategy": "fifo",
        "pre_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname herpa_derpa"],
            }
        ],
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname dog"],
            }
        ],
    }
    res = helper.post_and_check_errors("/setconfig", pl)
    assert len(res) == 0


@pytest.mark.setconfig
def test_setconfig_napalm_pre_check_fail():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": "hostname cat",
        "queue_strategy": "fifo",
        "pre_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname cat"],
            }
        ],
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname dog"],
            }
        ],
    }
    res = helper.post_and_check_errors("/setconfig", pl)
    assert len(res) > 0


@pytest.mark.setconfig
def test_setconfig_napalm_post_check_fail():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": "hostname cat",
        "queue_strategy": "fifo",
        "pre_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname dog"],
            }
        ],
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {"command": "show run | i hostname"},
                "match_str": ["hostname dog"],
            }
        ],
    }
    res = helper.post_and_check_errors("/setconfig", pl)
    assert len(res) > 0


@pytest.mark.setconfig
def test_setconfig_napalm_multiple():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": ["hostname meowcat", "no ip domain lookup"],
    }
    res = helper.post_and_check("/setconfig", pl)
    assert len(res["changes"]) > 1


@pytest.mark.setconfig
def test_setconfig_napalm_multiple_j2():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "j2config": {"template": "test", "args": {"vlans": ["1", "2", "3"]}},
    }
    res = helper.post_and_check("/setconfig", pl)
    assert len(res["changes"]) > 3


@pytest.mark.setconfig
def test_setconfig_napalm_dry_run():
    pl = {
        "library": "napalm",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "j2config": {"template": "test", "args": {"vlans": ["1", "2", "3"]}},
    }
    res = helper.post_and_check("/setconfig", pl)
    assert len(res["changes"]) > 3


@pytest.mark.setconfig
@pytest.mark.cisgoalternate
def test_setconfig_netmiko():
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
    if matchstr in res["changes"]:
        assert True
    else:
        assert False


@pytest.mark.setconfig
@pytest.mark.cisgoalternate
def test_setconfig_netmiko_multiple():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "config": ["hostname yeti", "hostname bufoon"],
    }
    res = helper.post_and_check("/setconfig", pl)
    matchstr = r + "#"
    assert len(res["changes"]) > 4


@pytest.mark.setconfig
@pytest.mark.cisgoalternate
def test_setconfig_netmiko_j2():
    pl = {
        "library": "netmiko",
        "connection_args": {
            "device_type": "cisco_ios",
            "host": helper.test_device_ios_cli,
            "username": "admin",
            "password": "admin",
        },
        "j2config": {"template": "test", "args": {"vlans": ["1", "2", "3"]}},
    }
    res = helper.post_and_check("/setconfig", pl)
    assert len(res["changes"]) > 6


@pytest.mark.setconfig
def test_setconfig_ncclient():
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
            "target": "running",
            "config": "<nc:config xmlns:nc='urn:ietf:params:xml:ns:netconf:base:1.0'><configure xmlns='http://www.cisco.com/nxos:1.0:vlan_mgr_cli'><__XML__MODE__exec_configure><interface><ethernet><interface>helloworld</interface><__XML__MODE_if-ethernet-switch><switchport><trunk><allowed><vlan><add><__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans><add-vlans>99</add-vlans></__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans></add></vlan></allowed></trunk></switchport></__XML__MODE_if-ethernet-switch></ethernet></interface></__XML__MODE__exec_configure></configure></nc:config>",
        },
    }
    res = helper.post_and_check("/setconfig", pl)
    assert res == 'Namespace="http://www.cisco.com/nxos:1.0:vlan_mgr_cli"'


@pytest.mark.setconfig
def test_setconfig_ncclient_j2():
    pl = {
        "library": "ncclient",
        "connection_args": {
            "host": helper.test_device_netconf,
            "username": "admin",
            "password": "admin",
            "port": 830,
            "hostkey_verify": False,
        },
        "j2config": {
            "template": "ncclient_test",
            "args": {"vlans": ["10", "20", "30"]}
        },
    }
    res = helper.post_and_check("/setconfig", pl)
    assert res == 'Namespace="http://www.cisco.com/nxos:1.0:vlan_mgr_cli"'

@pytest.mark.setconfig
def test_setconfig_restconf_post():
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
            "action": "post",
            "payload": {
                "Cisco-IOS-XE-native:BDI": {"name": "4001", "description": "netpalm"}
            },
        },
    }
    res = helper.post_and_check("/setconfig", pl)
    assert (
        res[
            "https://ios-xe-mgmt-latest.cisco.com:9443/restconf/data/Cisco-IOS-XE-native:native/interface/"
        ]["status_code"]
        == 201
    )


@pytest.mark.setconfig
def test_setconfig_restconf_patch():
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
            "uri": "/restconf/data/Cisco-IOS-XE-native:native/interface/BDI=4001",
            "action": "patch",
            "payload": {
                "Cisco-IOS-XE-native:BDI": {
                    "name": "4001",
                    "description": "netpalm - namechange",
                }
            },
        },
    }
    res = helper.post_and_check("/setconfig", pl)
    assert (
        res[
            "https://ios-xe-mgmt-latest.cisco.com:9443/restconf/data/Cisco-IOS-XE-native:native/interface/BDI=4001"
        ]["status_code"]
        == 204
    )


@pytest.mark.setconfig
def test_setconfig_restconf_delete():
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
            "uri": "/restconf/data/Cisco-IOS-XE-native:native/interface/BDI=4001",
            "action": "delete",
        },
    }
    res = helper.post_and_check("/setconfig", pl)
    assert (
        res[
            "https://ios-xe-mgmt-latest.cisco.com:9443/restconf/data/Cisco-IOS-XE-native:native/interface/BDI=4001"
        ]["status_code"]
        == 204
    )

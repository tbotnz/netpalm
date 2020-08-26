import logging
from typing import List, Union

import pytest

from tests.helper import netpalm_testhelper

log = logging.getLogger(__name__)
helper = netpalm_testhelper()

CISGO_DEFAULT_HOSTNAME = "cisgo1000v"


def cisgo_port_number():
    yield from range(10000, 10030)


cisgo_port_number = cisgo_port_number()


class CisgoHelper:
    def __init__(self):
        self.hostname = "cisgo"
        self.port_number = next(cisgo_port_number)
        self.clean()

    def clean(self):
        pl = {
            "library": "netmiko",
            "connection_args": self.netmiko_connection_args,
            "command": "reset state"
        }
        result = helper.post_and_check('/getconfig', pl)

    @property
    def netmiko_connection_args(self):
        return {
            "device_type": "cisco_ios",
            "host": self.hostname,
            "port": self.port_number,
            "username": "admin",
            "password": "admin",
            "fast_cli": True,
            "default_enter": "\r\n",
        }

    @property
    def napalm_connection_args(self):
        return {
            "device_type": "cisco_ios",
            "host": self.hostname,
            "username": "admin",
            "password": "admin",
            "optional_args": {
                "port": self.port_number,
                "fast_cli": True,
                "default_enter": "\r\n"
            }
        }


@pytest.fixture(scope="module")
def cisgo_helper():
    return CisgoHelper()


def hostname_from_config(config_lines: Union[List[str], str]) -> str:
    if isinstance(config_lines, str):
        config_lines = config_lines.splitlines()

    for line in config_lines:
        if not line:
            continue
        command, *args = line.split()
        if command == "hostname":
            hostname = ' '.join(args)  # this will false-match if there's weird whitespace in hostname like \t, etc
            break

    else:
        raise ValueError("No hostname found!")

    return hostname


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "command": "show running-config"
    }
    res = helper.post_and_check('/getconfig', pl)
    assert hostname_from_config(res["show running-config"]) == CISGO_DEFAULT_HOSTNAME


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko_with_textfsm(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "command": "show ip interface brief",
        "args": {
            "use_textfsm": True
        }
    }
    res = helper.post_and_check('/getconfig', pl)
    assert res["show ip interface brief"][0]["status"] == "up"


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko_multiple(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "command": ["show running-config", "show ip interface brief"]
    }
    res = helper.post_and_check('/getconfig', pl)
    assert len(res["show ip interface brief"]) > 1
    assert hostname_from_config(res["show running-config"]) == CISGO_DEFAULT_HOSTNAME


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_napalm_multiple(cisgo_helper: CisgoHelper):
    pl = {
        "connection_args": cisgo_helper.napalm_connection_args,
        "library": "napalm",
        "command": ["show running-config", "show ip interface brief"]
    }
    res = helper.post_and_check('/getconfig', pl)
    log.error(res)
    assert len(res["show ip interface brief"]) > 1
    assert hostname_from_config(res["show running-config"])


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_napalm_getter(cisgo_helper: CisgoHelper):
    pl = {
        "library": "napalm",
        "connection_args": cisgo_helper.napalm_connection_args,
        "command": "get_facts"
    }
    res = helper.post_and_check('/getconfig', pl)
    log.error(res["get_facts"])
    assert res["get_facts"]["hostname"] == CISGO_DEFAULT_HOSTNAME


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_napalm(cisgo_helper: CisgoHelper):
    pl = {
        "library": "napalm",
        "connection_args": cisgo_helper.napalm_connection_args,
        "command": "show running-config"
    }
    res = helper.post_and_check('/getconfig', pl)

    assert hostname_from_config(res["show running-config"])


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko_post_check(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "command": "show running-config",
        "queue_strategy": "pinned",
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {
                    "command": "show running-config"
                },
                "match_str": [
                    "hostname " + CISGO_DEFAULT_HOSTNAME
                ]
            }
        ]
    }
    errors = helper.post_and_check_errors('/getconfig', pl)
    assert len(errors) == 0
    pl["post_checks"][0]["match_str"][0] += "asdf"
    errors = helper.post_and_check_errors('/getconfig', pl)
    assert len(errors) > 0


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_netmiko_post_check_fails(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "command": "show running-config",
        "queue_strategy": "pinned",
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {
                    "command": "show running-config"
                },
                "match_str": [
                    "hostname " + CISGO_DEFAULT_HOSTNAME + "DEFINITELY WRONG"
                ]
            }
        ]
    }
    errors = helper.post_and_check_errors('/getconfig', pl)
    assert len(errors) > 0


@pytest.mark.getconfig
@pytest.mark.cisgo
def test_getconfig_napalm_post_check(cisgo_helper: CisgoHelper):
    pl = {
        "library": "napalm",
        "connection_args": cisgo_helper.napalm_connection_args,
        "command": "show run | i hostname",
        "queue_strategy": "pinned",
        "post_checks": [
            {
                "match_type": "include",
                "get_config_args": {
                    "command": "show running-config"
                },
                "match_str": [
                    "hostname " + CISGO_DEFAULT_HOSTNAME
                ]
            }
        ]
    }
    errors = helper.post_and_check_errors('/getconfig', pl)
    assert len(errors) == 0

import logging
import random
from typing import List, Union

import pytest

from tests.helper import netpalm_testhelper

log = logging.getLogger(__name__)
helper = netpalm_testhelper()

CISGO_DEFAULT_HOSTNAME = "cisgo1000v"
CISGO_NEW_HOSTNAME = CISGO_DEFAULT_HOSTNAME.upper() + str(random.randint(100, 900))


def cisgo_port_number():
    yield from range(10000, 10050)


cisgo_port_number = cisgo_port_number()


def netmiko_connection_args():
    return {
        "device_type": "cisco_ios",
        "host": helper.test_device_cisgo,
        "port": next(cisgo_port_number),
        "username": "admin",
        "password": "admin",
        "fast_cli": True,
        "default_enter": "\r\n"
    }


def napalm_connection_args():
    return {
        "device_type": "cisco_ios",
        "host": helper.test_device_cisgo,
        "username": "admin",
        "password": "admin",
        "optional_args": {
            "port": next(cisgo_port_number),
            "fast_cli": True,
            "default_enter": "\r\n"
        }
    }


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


def get_hostname(connection_args):
    pl = {
        "library": "netmiko",
        "connection_args": connection_args,
        "command": "show running-config"
    }
    res = helper.post_and_check('/getconfig', pl)
    return hostname_from_config(res["show running-config"])


@pytest.mark.setconfig
@pytest.mark.cisgo
def test_setconfig_netmiko():
    pl = {
        "library": "netmiko",
        "connection_args": netmiko_connection_args(),
        "config": ["hostname " + CISGO_NEW_HOSTNAME],
        "enable_mode": True
    }
    res = helper.post_and_check('/setconfig', pl)
    matchstr = CISGO_NEW_HOSTNAME + "#"
    assert matchstr in res["changes"]

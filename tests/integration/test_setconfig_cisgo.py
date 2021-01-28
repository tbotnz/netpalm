import logging
import random
from typing import List, Union

import pytest

from .helper import NetpalmTestHelper
from .test_getconfig_cisgo import CisgoHelper

log = logging.getLogger(__name__)
helper = NetpalmTestHelper()

CISGO_DEFAULT_HOSTNAME = "cisshgo1000v"
CISGO_NEW_HOSTNAME = CISGO_DEFAULT_HOSTNAME.upper() + str(random.randint(100, 900))


@pytest.fixture(scope="function")
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
def test_setconfig_netmiko(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "config": ["hostname " + CISGO_NEW_HOSTNAME],
        "enable_mode": True
    }
    res = helper.post_and_check('/setconfig', pl)
    matchstr = CISGO_NEW_HOSTNAME + "#"
    assert matchstr in res["changes"]


@pytest.mark.setconfig
@pytest.mark.cisgo
def test_setconfig_netmiko_multiple(cisgo_helper: CisgoHelper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "config": ["hostname yeti", "hostname bufoon"],
        "enable_mode": True
    }
    res = helper.post_and_check('/setconfig', pl)
    assert len(res["changes"]) > 4


@pytest.mark.setconfig
@pytest.mark.cisgo
def test_setconfig_netmiko_j2(cisgo_helper):
    pl = {
        "library": "netmiko",
        "connection_args": cisgo_helper.netmiko_connection_args,
        "enable_mode": True,
        "j2config": {
            "template": "test",
            "args": {
                "vlans": ["1", "2", "3"]
            }
        }
    }
    res = helper.post_and_check('/setconfig', pl)
    assert len(res["changes"]) > 6

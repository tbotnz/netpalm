from __future__ import annotations

import logging
from typing import Any

import napalm
from netpalm.backend.core.driver.netpalm_driver import NetpalmDriver
from netpalm.backend.core.utilities.rediz_meta import write_meta_error

log = logging.getLogger(__name__)


class naplm(NetpalmDriver):
    driver_name = "napalm"

    def __init__(self, **kwargs: Any) -> None:
        log.debug(f"initializing napalm driver with args: {kwargs}")
        self.connection_args = kwargs.get("connection_args", False)
        # convert the netmiko naming format to the native napalm format
        driver_lookup = {
            "arista_eos": "eos",
            "juniper": "junos",
            "cisco_xr": "iosxr",
            "nxos": "nxos",
            "cisco_nxos_ssh": "nxos_ssh",
            "cisco_ios": "ios",
        }
        self.driver = driver_lookup[self.connection_args.get("device_type", False)]
        self.connection_args["hostname"] = self.connection_args.pop("host")
        del self.connection_args["device_type"]

    def connect(self) -> Any:
        try:
            driver = napalm.get_network_driver(self.driver)
            napalmses = driver(**self.connection_args)
            return napalmses
        except Exception as e:
            write_meta_error(e)

    def sendcommand(self, session: Any = None, command: list[str] | Any = None) -> dict[str, Any]:
        log.debug(f"running send command on napalm driver: {session} {command}")
        try:
            result = {}
            session.open()
            for c in command:
                if hasattr(session, str(c)):
                    response = getattr(session, str(c))()
                    result[c] = response
                else:
                    response = session.cli([c])
                    result[c] = response[c].split("\n")
            return result
        except Exception as e:
            write_meta_error(e)

    def config(
        self, session: Any = None, command: str | list[str] | Any = None, dry_run: bool = False, **kwargs: Any
    ) -> dict[str, Any]:
        try:
            if type(command) == list:
                napalmconfig = ""
                for comm in command:
                    napalmconfig += comm + "\n"
            else:
                napalmconfig = command
            session.open()
            session.load_merge_candidate(config=napalmconfig)
            diff = session.compare_config()
            if dry_run:
                response = session.discard_config()
            else:
                response = session.commit_config()
            result = {}
            result["changes"] = diff.split("\n")
            return result
        except Exception as e:
            write_meta_error(e)

    def logout(self, session: Any) -> None:
        try:
            response = session.close()
            return response
        except Exception as e:
            write_meta_error(e)

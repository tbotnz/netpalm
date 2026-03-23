from __future__ import annotations

import logging

from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func
from netpalm.exceptions import NetpalmCheckError

from netpalm.backend.core.driver import driver_map

log = logging.getLogger(__name__)


def exec_command(**kwargs):
    """Execute getconfig commands via the appropriate southbound driver."""
    lib = kwargs.get("library", False)
    command = kwargs.get("command", False)
    webhook = kwargs.get("webhook", False)
    post_checks = kwargs.get("post_checks", False)

    if not driver_map.get(lib):
        raise NotImplementedError(f"unknown driver '{lib}'")

    commandlst = [command] if isinstance(command, str) else command

    result = {}
    driver_obj = driver_map[lib](**kwargs)
    sesh = driver_obj.connect()

    if commandlst:
        result = driver_obj.sendcommand(sesh, commandlst)
    else:
        result = driver_obj.sendcommand(sesh)

    if post_checks:
        for postcheck in post_checks:
            cmd = postcheck["get_config_args"]["command"]
            post_check_result = driver_obj.sendcommand(sesh, [cmd])
            for matchstr in postcheck["match_str"]:
                if postcheck["match_type"] == "include" and matchstr not in str(post_check_result):
                    raise NetpalmCheckError(f"PostCheck Failed: {matchstr} not found in {post_check_result}")
                if postcheck["match_type"] == "exclude" and matchstr in str(post_check_result):
                    raise NetpalmCheckError(f"PostCheck Failed: {matchstr} found in {post_check_result}")

    driver_obj.logout(sesh)

    if webhook:
        exec_webhook_func(jobdata={"task_result": result}, webhook_payload=webhook)

    return result

"""
exec_config — executes setconfig commands via the appropriate southbound driver.
"""
from __future__ import annotations

from netpalm.backend.core.utilities.jinja2.j2 import render_j2template
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func
from netpalm.exceptions import NetpalmCheckError

from netpalm.backend.core.driver import driver_map


def exec_config(**kwargs):
    """Execute setconfig commands via the appropriate southbound driver."""
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf = kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)
    pre_checks = kwargs.get("pre_checks", False)
    post_checks = kwargs.get("post_checks", False)
    enable_mode = kwargs.get("enable_mode", False)

    if j2conf:
        j2confargs = j2conf.get("args")
        res = render_j2template(j2conf["template"], template_type="config", kwargs=j2confargs)
        config = res["data"]["task_result"]["template_render_result"]
        if j2conf and config and lib == "ncclient":
            if not kwargs.get("args", False):
                kwargs["args"] = {}
            kwargs["args"]["config"] = config

    if not driver_map.get(lib):
        raise NotImplementedError(f"unknown driver '{lib}'")

    driver_obj = driver_map[lib](**kwargs)
    sesh = driver_obj.connect()

    if pre_checks:
        for precheck in pre_checks:
            cmd = precheck["get_config_args"]["command"]
            pre_check_result = driver_obj.sendcommand(sesh, [cmd])
            for matchstr in precheck["match_str"]:
                if precheck["match_type"] == "include" and matchstr not in str(pre_check_result):
                    raise NetpalmCheckError(f"PreCheck Failed: {matchstr} not found in {pre_check_result}")
                if precheck["match_type"] == "exclude" and matchstr in str(pre_check_result):
                    raise NetpalmCheckError(f"PreCheck Failed: {matchstr} found in {pre_check_result}")

    result = driver_obj.config(sesh, config, enable_mode) if enable_mode else driver_obj.config(sesh, config)

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

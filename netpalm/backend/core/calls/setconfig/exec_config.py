from netpalm.backend.core.utilities.rediz_meta import (
    render_netpalm_payload,
    write_mandatory_meta,
    write_meta_error,
)
from netpalm.backend.core.utilities.jinja2.j2 import render_j2template
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func
from netpalm.exceptions import NetpalmCheckError

from netpalm.backend.core.mongo.utils import write_task_result

from netpalm.backend.core.driver import driver_map


def exec_config(**kwargs):
    """main function for executing setconfig commands to southbound drivers"""
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf = kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)
    pre_checks = kwargs.get("pre_checks", False)
    post_checks = kwargs.get("post_checks", False)
    enable_mode = kwargs.get("enable_mode", False)

    result = False
    pre_check_ok = True

    try:
        write_mandatory_meta()

        if j2conf:
            j2confargs = j2conf.get("args")
            res = render_j2template(
                j2conf["template"], template_type="config", kwargs=j2confargs
            )
            config = res["data"]["task_result"]["template_render_result"]

            if (
                j2conf and config and lib == "ncclient"
            ):  # move this into the driver in future
                if not kwargs.get("args", False):
                    kwargs["args"] = {}
                kwargs["args"]["config"] = config

        if not driver_map.get(lib):
            raise NotImplementedError(f"unknown 'driver' {lib}")

        if not pre_checks and not post_checks:
            driver_obj = driver_map[lib](**kwargs)
            sesh = driver_obj.connect()
            if enable_mode:
                result = driver_obj.config(sesh, config, enable_mode)
            else:
                result = driver_obj.config(sesh, config)
            driver_obj.logout(sesh)

        else:
            driver_obj = driver_map[lib](**kwargs)
            sesh = driver_obj.connect()
            if pre_checks:
                for precheck in pre_checks:
                    command = precheck["get_config_args"]["command"]
                    pre_check_result = driver_obj.sendcommand(sesh, [command])
                    for matchstr in precheck["match_str"]:
                        if precheck["match_type"] == "include" and matchstr not in str(
                            pre_check_result
                        ):
                            raise NetpalmCheckError(
                                f"PreCheck Failed: {matchstr} not found in {pre_check_result}"
                            )
                        if precheck["match_type"] == "exclude" and matchstr in str(
                            pre_check_result
                        ):
                            raise NetpalmCheckError(
                                f"PreCheck Failed: {matchstr} found in {pre_check_result}"
                            )

            if pre_check_ok:
                result = driver_obj.config(sesh, config, enable_mode)
                if post_checks:
                    for postcheck in post_checks:
                        command = postcheck["get_config_args"]["command"]
                        post_check_result = driver_obj.sendcommand(sesh, [command])
                        for matchstr in postcheck["match_str"]:
                            if postcheck[
                                "match_type"
                            ] == "include" and matchstr not in str(post_check_result):
                                raise NetpalmCheckError(
                                    f"PostCheck Failed: {matchstr} not found in {post_check_result}"
                                )
                            if postcheck["match_type"] == "exclude" and matchstr in str(
                                post_check_result
                            ):
                                raise NetpalmCheckError(
                                    f"PostCheck Failed: {matchstr} found in {post_check_result}"
                                )
            driver_obj.logout(sesh)

        if webhook:
            current_jobdata = render_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)

    except Exception as e:
        write_meta_error(e)

    write_task_result(result_payload=res)
    return result

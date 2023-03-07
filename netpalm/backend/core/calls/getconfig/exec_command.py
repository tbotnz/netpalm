import logging

from netpalm.backend.core.utilities.rediz_meta import (
    render_netpalm_payload,
    write_mandatory_meta,
)
from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func
from netpalm.exceptions import NetpalmCheckError

from netpalm.backend.core.driver import driver_map

log = logging.getLogger(__name__)


def exec_command(**kwargs):
    """main function for executing getconfig commands to southbound drivers"""
    lib = kwargs.get("library", False)
    command = kwargs.get("command", False)
    webhook = kwargs.get("webhook", False)
    post_checks = kwargs.get("post_checks", False)

    result = False

    if type(command) == str:
        commandlst = [command]
    else:
        commandlst = command

    log.debug(f"driver_map: {driver_map}")

    if not driver_map.get(lib):
        raise NotImplementedError(f"unknown 'driver' {lib}")

    try:
        write_mandatory_meta()
        if not post_checks:
            result = {}

            driver_obj = driver_map[lib](**kwargs)
            sesh = driver_obj.connect()
            if commandlst:
                result = driver_obj.sendcommand(sesh, commandlst)
            else:
                result = driver_obj.sendcommand(sesh)
            driver_obj.logout(sesh)

        else:
            result = {}
            driver_obj = driver_map[lib](**kwargs)
            sesh = driver_obj.connect()
            if commandlst:
                result = driver_obj.sendcommand(sesh, commandlst)
            if post_checks:
                for postcheck in post_checks:
                    command = postcheck["get_config_args"]["command"]
                    post_check_result = driver_obj.sendcommand(sesh, [command])
                    for matchstr in postcheck["match_str"]:
                        if postcheck["match_type"] == "include" and matchstr not in str(
                            post_check_result
                        ):
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

    return result

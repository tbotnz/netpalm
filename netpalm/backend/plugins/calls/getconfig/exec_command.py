import logging

from netpalm.backend.core.utilities.rediz_meta import render_netpalm_payload, write_mandatory_meta
from netpalm.backend.core.utilities.rediz_meta import write_meta_error_string, write_meta_error
from netpalm.backend.plugins.drivers.napalm.napalm_drvr import naplm
from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from netpalm.backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from netpalm.backend.plugins.drivers.puresnmp.puresnmp_drvr import pursnmp
from netpalm.backend.plugins.drivers.restconf.restconf import restconf
from netpalm.backend.plugins.utilities.webhook.webhook import exec_webhook_func

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

    try:
        write_mandatory_meta()
        if not post_checks:
            result = {}
            if lib == "netmiko":
                netmik = netmko(**kwargs)
                sesh = netmik.connect()
                result = netmik.sendcommand(sesh, commandlst)
                netmik.logout(sesh)
            elif lib == "napalm":
                napl = naplm(**kwargs)
                sesh = napl.connect()
                result = napl.sendcommand(sesh, commandlst)
                napl.logout(sesh)
            elif lib == "puresnmp":
                snm = pursnmp(**kwargs)
                sesh = snm.connect()
                result = snm.sendcommand(sesh, commandlst)
                snm.logout(sesh)
            elif lib == "ncclient":
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.getconfig(sesh)
                ncc.logout(sesh)
            elif lib == "restconf":
                rc = restconf(**kwargs)
                sesh = rc.connect()
                result = rc.sendcommand(sesh)
                rc.logout(sesh)
            else:
                raise NotImplementedError(f"unknown 'library' parameter {lib}")

        else:
            result = {}
            if lib == "netmiko":
                netmik = netmko(**kwargs)
                sesh = netmik.connect()
                if commandlst:
                    result = netmik.sendcommand(sesh, commandlst)
                if post_checks:
                    for postcheck in post_checks:
                        command = postcheck["get_config_args"]["command"]
                        post_check_result = netmik.sendcommand(sesh, [command])
                        for matchstr in postcheck["match_str"]:
                            if postcheck["match_type"] == "include" and matchstr not in str(post_check_result):
                                write_meta_error_string(f"PostCheck Failed: {matchstr} not found in {post_check_result}")
                            if postcheck["match_type"] == "exclude" and matchstr in str(post_check_result):
                                write_meta_error_string(f"PostCheck Failed: {matchstr} found in {post_check_result}")
                netmik.logout(sesh)
            elif lib == "napalm":
                napl = naplm(**kwargs)
                sesh = napl.connect()
                if commandlst:
                    result = napl.sendcommand(sesh, commandlst)
                if post_checks:
                    for postcheck in post_checks:
                        command = postcheck["get_config_args"]["command"]
                        post_check_result = napl.sendcommand(sesh, [command])
                        for matchstr in postcheck["match_str"]:
                            if postcheck["match_type"] == "include" and matchstr not in str(post_check_result):
                                write_meta_error_string(f"PostCheck Failed: {matchstr} not found in {post_check_result}")
                            if postcheck["match_type"] == "exclude" and matchstr in str(post_check_result):
                                write_meta_error_string(f"PostCheck Failed: {matchstr} found in {post_check_result}")
                napl.logout(sesh)
            elif lib == "ncclient":
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.getconfig(sesh)
                ncc.logout(sesh)
            elif lib == "restconf":
                rc = restconf(**kwargs)
                sesh = rc.connect()
                result = rc.sendcommand(sesh)
                rc.logout(sesh)

        if webhook:
            current_jobdata = render_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
    except Exception as e:
        write_meta_error(e)

    return result

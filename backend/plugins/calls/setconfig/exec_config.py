from napalm.base.mock import raise_exception
from backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from backend.plugins.drivers.napalm.napalm_drvr import naplm
from backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from backend.plugins.drivers.restconf.restconf import restconf

from backend.plugins.utilities.jinja2.j2 import render_j2template

from backend.plugins.utilities.webhook.webhook import exec_webhook_func

from backend.core.meta.rediz_meta import prepare_netpalm_payload
from backend.core.meta.rediz_meta import write_meta_error

def exec_config(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf =  kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)
    pre_checks = kwargs.get("pre_checks", False)
    post_checks = kwargs.get("post_checks", False)

    result = False
    pre_check_ok = True
    
    if j2conf:
        j2confargs = j2conf.get("args")
        try:
            res = render_j2template(j2conf["template"], template_type="config", kwargs=j2confargs)
            config = res["data"]["task_result"]["template_render_result"]
        except Exception as e:
            config = False
            write_meta_error(str(e))

    if not pre_checks and not post_checks:
        try:
            if lib == "netmiko":
                netmik = netmko(**kwargs)
                sesh = netmik.connect()
                result = netmik.config(sesh,config)
                netmik.logout(sesh)
            elif lib == "napalm":
                napl = naplm(**kwargs)
                sesh = napl.connect()
                result = napl.config(sesh,config)
                napl.logout(sesh)
            elif lib == "ncclient":
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.editconfig(sesh)
                ncc.logout(sesh)
            elif lib == "restconf":
                rcc = restconf(**kwargs)
                sesh = rcc.connect()
                result = rcc.config(sesh)
                rcc.logout(sesh)
        except Exception as e:
            write_meta_error(str(e))

    else:
        try:
            if lib == "netmiko":
                netmik = netmko(**kwargs)
                sesh = netmik.connect()
                if pre_checks:
                    for precheck in pre_checks:
                        command = precheck["get_config_args"]["command"]
                        pre_check_result = netmik.sendcommand(sesh,[command])
                        for matchstr in precheck["match_str"]:
                            if precheck["match_type"] == "include" and matchstr not in str(pre_check_result):
                                write_meta_error("PreCheck Failed: " + matchstr + " not found in " + str(pre_check_result))
                                pre_check_ok = False
                            if precheck["match_type"] == "exclude" and matchstr in str(pre_check_result):
                                write_meta_error("PreCheck Failed: " + matchstr + " found in " + str(pre_check_result))
                                pre_check_ok = False
                if pre_check_ok:
                    result = netmik.config(sesh,config)
                    if post_checks:
                        for postcheck in post_checks:
                            command = postcheck["get_config_args"]["command"]
                            post_check_result = netmik.sendcommand(sesh,[command])
                            for matchstr in postcheck["match_str"]:
                                if postcheck["match_type"] == "include" and matchstr not in str(post_check_result):
                                    write_meta_error("PostCheck Failed: " + matchstr + " not found in " + str(post_check_result))
                                if postcheck["match_type"] == "exclude" and matchstr in str(post_check_result):
                                    write_meta_error("PostCheck Failed: " + matchstr + " found in " + str(post_check_result))
                netmik.logout(sesh)

            elif lib == "napalm":
                napl = naplm(**kwargs)
                sesh = napl.connect()
                if pre_checks:
                    for precheck in pre_checks:
                        command = precheck["get_config_args"]["command"]
                        pre_check_result = napl.sendcommand(sesh,[command])
                        for matchstr in precheck["match_str"]:
                            if precheck["match_type"] == "include" and matchstr not in str(pre_check_result):
                                write_meta_error("PreCheck Failed: " + matchstr + " not found in " + str(pre_check_result))
                                pre_check_ok = False
                            if precheck["match_type"] == "exclude" and matchstr in str(pre_check_result):
                                write_meta_error("PreCheck Failed: " + matchstr + " found in " + str(pre_check_result))
                                pre_check_ok = False
                if pre_check_ok:
                    result = napl.config(sesh,config)
                    if post_checks:
                        for postcheck in post_checks:
                            command = postcheck["get_config_args"]["command"]
                            post_check_result = napl.sendcommand(sesh,[command])
                            for matchstr in postcheck["match_str"]:
                                if postcheck["match_type"] == "include" and matchstr not in str(post_check_result):
                                    write_meta_error("PostCheck Error" + matchstr + " not found in " + str(post_check_result))
                                if postcheck["match_type"] == "exclude" and matchstr in str(post_check_result):
                                    write_meta_error("PostCheck Error" + matchstr + " found in " + str(post_check_result))
                napl.logout(sesh)

            elif lib == "ncclient":
                ncc = ncclien(**kwargs)
                sesh = ncc.connect()
                result = ncc.editconfig(sesh)
                ncc.logout(sesh)
            elif lib == "restconf":
                rcc = restconf(**kwargs)
                sesh = rcc.connect()
                result = rcc.config(sesh)
                rcc.logout(sesh)
        except Exception as e:
            write_meta_error(str(e))        

    try:
        if webhook:
            current_jobdata = prepare_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
    except Exception as e:
        write_meta_error(str(e))
            
    return result
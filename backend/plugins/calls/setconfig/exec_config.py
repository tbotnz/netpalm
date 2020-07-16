from backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from backend.plugins.drivers.napalm.napalm_drvr import naplm
from backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from backend.plugins.drivers.restconf.restconf import restconf

from backend.plugins.management.jinja2.j2 import render_j2template

from backend.plugins.calls.webhook.webhook import exec_webhook_func
from backend.core.meta.rediz_meta import prepare_netpalm_payload

def exec_config(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf =  kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)

    if j2conf:
        j2confargs = j2conf.get("args")
        try:
            res = render_j2template(j2conf["template"], kwargs=j2confargs)
            config = res["data"]["task_result"]["template_render_result"]
        except Exception as e:
            config = False
            return str(e)

    try:
        result = False
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
        if webhook:
            current_jobdata = prepare_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
        return result

    except Exception as e:
        return str(e)
from backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from backend.plugins.drivers.napalm.napalm_drvr import naplm
from backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from backend.plugins.drivers.restconf.restconf import restconf

from backend.plugins.utilities.webhook.webhook import exec_webhook_func

from backend.core.meta.rediz_meta import prepare_netpalm_payload
from backend.core.meta.rediz_meta import write_meta_error


def exec_command(**kwargs):
    lib = kwargs.get("library", False)
    command = kwargs.get("command", False)
    webhook = kwargs.get("webhook", False)
    result = False

    if type(command) == str:
        commandlst = [command]
    else:
        commandlst = command

    try:
        result = {}
        if lib == "netmiko":
            netmik = netmko(**kwargs)
            sesh = netmik.connect()
            result = netmik.sendcommand(sesh,commandlst)
            netmik.logout(sesh)
        elif lib == "napalm":
            napl = naplm(**kwargs)
            sesh = napl.connect()
            result = napl.sendcommand(sesh,commandlst)
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
    except Exception as e:
        write_meta_error(str(e))

    try:
        if webhook:
            current_jobdata = prepare_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
            
    except Exception as e:
        write_meta_error(str(e))
        
    return result
from backend.plugins.netmiko.netmiko_drvr import netmko
from backend.plugins.napalm.napalm_drvr import naplm
from backend.plugins.ncclient.ncclient_drvr import ncclien
from backend.plugins.restconf.restconf import restconf
from backend.plugins.webhook.webhook import exec_webhook_func

from backend.core.redis.rediz_meta import prepare_netpalm_payload

def exec_command(**kwargs):
    lib = kwargs.get("library", False)
    command = kwargs.get("command", False)
    webhook = kwargs.get("webhook", False)

    if type(command) == str:
        commandlst = [command]
    else:
        commandlst = command

    try:
        result = False
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
        if webhook:
            current_jobdata = prepare_netpalm_payload()
            exec_webhook_func(jobdata=current_jobdata, kwargs=webhook)
        return result

    except Exception as e:
        return str(e)
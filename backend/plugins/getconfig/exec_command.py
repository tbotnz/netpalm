from backend.plugins.netmiko.netmiko_drvr import netmko
from backend.plugins.napalm.napalm_drvr import naplm
from backend.plugins.ncclient.ncclient_drvr import ncclien

def exec_command(**kwargs):
    lib = kwargs.get("library", False)
    command = kwargs.get("command", False)
    if type(command) == str:
        commandlst = [command]
    else:
        commandlst = command
    if lib == "netmiko":
        try:
            netmik = netmko(**kwargs)
            sesh = netmik.connect()
            result = netmik.sendcommand(sesh,commandlst)
            netmik.logout(sesh)
            return result
        except Exception as e:
            return str(e)
    elif lib == "napalm":
        try:
            napl = naplm(**kwargs)
            sesh = napl.connect()
            result = napl.sendcommand(sesh,commandlst)
            napl.logout(sesh)
            return result
        except Exception as e:
            return str(e)
    elif lib == "ncclient":
        try:
            ncc = ncclien(**kwargs)
            sesh = ncc.connect()
            result = ncc.getconfig(sesh)
            ncc.logout(sesh)
            return result
        except Exception as e:
            return str(e)
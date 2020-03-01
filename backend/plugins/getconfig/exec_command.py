from backend.plugins.netmiko.netmiko_drvr import netmko
from backend.plugins.napalm.napalm_drvr import naplm

def exec_command(**kwargs):
    lib = kwargs.get("library", False)
    command = kwargs.get("command", False)
    if type(command) == str:
        commandlst = [command]
    else:
        commandlst = command
    if lib == "netmiko":
        netmik = netmko(**kwargs)
        sesh = netmik.connect()
        result = netmik.sendcommand(sesh,commandlst)
        netmik.logout(sesh)
        return result
    elif lib == "napalm":
        napl = naplm(**kwargs)
        sesh = napl.connect()
        result = napl.sendcommand(sesh,commandlst)
        napl.logout(sesh)
        return result
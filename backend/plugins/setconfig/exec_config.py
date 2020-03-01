from backend.plugins.netmiko.netmiko_drvr import netmko
from backend.plugins.napalm.napalm_drvr import naplm

def exec_config(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    if lib == "netmiko":
        netmik = netmko(**kwargs)
        sesh = netmik.connect()
        result = netmik.config(sesh,config)
        netmik.logout(sesh)
        return result
    elif lib == "napalm":
        napl = naplm(**kwargs)
        sesh = napl.connect()
        result = napl.config(sesh,config)
        napl.logout(sesh)
        return result

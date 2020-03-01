from backend.plugins.netmiko.netmiko_drvr import netmko
from backend.plugins.napalm.napalm_drvr import naplm

def exec_config(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    if lib == "netmiko":
        try:
            netmik = netmko(**kwargs)
            sesh = netmik.connect()
            result = netmik.config(sesh,config)
            netmik.logout(sesh)
            return result
        except Exception as e:
            return e
    elif lib == "napalm":
        try:
            napl = naplm(**kwargs)
            sesh = napl.connect()
            result = napl.config(sesh,config)
            napl.logout(sesh)
            return result
        except Exception as e:
            return e
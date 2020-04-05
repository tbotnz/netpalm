from backend.plugins.netmiko.netmiko_drvr import netmko
from backend.plugins.napalm.napalm_drvr import naplm
from backend.plugins.ncclient.ncclient_drvr import ncclien
from backend.plugins.jinja2.j2 import render_j2template
from backend.plugins.restconf.restconf import restconf

def exec_config(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf =  kwargs.get("j2config", False)
    if j2conf:
        j2confargs = j2conf.get("args")
        try:
            res = render_j2template(j2conf["template"], kwargs=j2confargs)
            config = res["data"]["task_result"]["template_render_result"]
        except Exception as e:
            config = False
            return e
    if lib == "netmiko":
        try:
            netmik = netmko(**kwargs)
            sesh = netmik.connect()
            result = netmik.config(sesh,config)
            netmik.logout(sesh)
            return result
        except Exception as e:
            return str(e)
    elif lib == "napalm":
        try:
            napl = naplm(**kwargs)
            sesh = napl.connect()
            result = napl.config(sesh,config)
            napl.logout(sesh)
            return result
        except Exception as e:
            return str(e)
    elif lib == "ncclient":
        try:
            ncc = ncclien(**kwargs)
            sesh = ncc.connect()
            result = ncc.editconfig(sesh)
            ncc.logout(sesh)
            return result
        except Exception as e:
            return str(e)
    elif lib == "restconf":
        try:
            rcc = restconf(**kwargs)
            sesh = rcc.connect()
            result = rcc.config(sesh)
            rcc.logout(sesh)
            return result
        except Exception as e:
            return str(e)
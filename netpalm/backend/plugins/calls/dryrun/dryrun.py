from netpalm.backend.core.meta.rediz_meta import prepare_netpalm_payload
from netpalm.backend.core.meta.rediz_meta import write_meta_error
from netpalm.backend.plugins.drivers.napalm.napalm_drvr import naplm
from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from netpalm.backend.plugins.utilities.jinja2.j2 import render_j2template
from netpalm.backend.plugins.utilities.webhook.webhook import exec_webhook_func


def dryrun(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf =  kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)
    result = False
    
    if j2conf:
        j2confargs = j2conf.get("args")
        try:
            res = render_j2template(j2conf["template"], template_type="config", kwargs=j2confargs)
            config = res["data"]["task_result"]["template_render_result"]
        except Exception as e:
            config = False
            write_meta_error(f"{e}")

    try:
        result = {}
        if lib == "napalm":
            napl = naplm(**kwargs)
            sesh = napl.connect()
            result = napl.config(session=sesh,command=config,dry_run=True)
            napl.logout(sesh)
        elif lib == "ncclient":
            ncc = ncclien(**kwargs)
            sesh = ncc.connect()
            result = ncc.editconfig(session=sesh,dry_run=True)
            ncc.logout(sesh)
    except Exception as e:
        write_meta_error(f"{e}")

    try:
        if webhook:
            current_jobdata = prepare_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
    except Exception as e:
        write_meta_error(f"{e}")
                
    return result
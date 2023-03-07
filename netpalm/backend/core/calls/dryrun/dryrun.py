from netpalm.backend.core.utilities.rediz_meta import (
    render_netpalm_payload,
    write_mandatory_meta,
)
from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.plugins.drivers.napalm.napalm_drvr import naplm
from netpalm.backend.plugins.drivers.netmiko.netmiko_drvr import netmko
from netpalm.backend.plugins.drivers.ncclient.ncclient_drvr import ncclien
from netpalm.backend.core.utilities.jinja2.j2 import render_j2template
from netpalm.backend.core.utilities.webhook.webhook import exec_webhook_func


def dryrun(**kwargs):
    lib = kwargs.get("library", False)
    config = kwargs.get("config", False)
    j2conf = kwargs.get("j2config", False)
    webhook = kwargs.get("webhook", False)
    enable_mode = kwargs.get("enable_mode", False)
    result = False

    try:
        write_mandatory_meta()

        if j2conf:
            j2confargs = j2conf.get("args")
            res = render_j2template(
                j2conf["template"], template_type="config", kwargs=j2confargs
            )
            config = res["data"]["task_result"]["template_render_result"]

        result = {}
        if lib == "napalm":
            napl = naplm(**kwargs)
            sesh = napl.connect()
            result = napl.config(session=sesh, command=config, dry_run=True)
            napl.logout(sesh)
        elif lib == "ncclient":
            # if we rendered j2config, add it to the kwargs['args'] dict
            if j2conf and config:
                if not kwargs.get("args", False):
                    kwargs["args"] = {}
                kwargs["args"]["config"] = config
            ncc = ncclien(**kwargs)
            sesh = ncc.connect()
            result = ncc.editconfig(session=sesh, dry_run=True)
            ncc.logout(sesh)
        elif lib == "netmiko":
            netmik = netmko(**kwargs)
            sesh = netmik.connect()
            result = netmik.config(sesh, config, enable_mode, dry_run=True)
            netmik.logout(sesh)

        if webhook:
            current_jobdata = render_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)

    except Exception as e:
        write_meta_error(e)

    return result

import importlib

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.utilities.rediz_meta import render_netpalm_payload, write_mandatory_meta
from netpalm.backend.core.utilities.rediz_meta import write_meta_error
from netpalm.backend.plugins.utilities.webhook.webhook import exec_webhook_func


class script_kiddy:
    def __init__(self, **kwargs):
        self.scrp_path = config.custom_scripts
        self.kwarg = kwargs.get('kwargs', False)
        self.arg = self.kwarg.get('args', False)
        self.script = self.kwarg.get('script', False)
        self.script_name = self.scrp_path.replace('/', '.') + self.script

    def s_exec(self):
        module = importlib.import_module(self.script_name)
        runscrp = getattr(module, "run")
        res = runscrp(kwargs=self.arg)
        return res


def script_exec(**kwargs):
    webhook = kwargs.get("webhook", False)
    result = False

    try:
        write_mandatory_meta()
        scrip = script_kiddy(kwargs=kwargs)
        result = scrip.s_exec()

        if webhook:
            current_jobdata = render_netpalm_payload(job_result=result)
            exec_webhook_func(jobdata=current_jobdata, webhook_payload=webhook)
    except Exception as e:
        write_meta_error(e)

    return result

from backend.core.confload.confload import config

import importlib

class webhook_runner:
    
    def __init__(self, **kwargs):
        self.webhook_dir_path = config().custom_webhooks
        self.kwarg = kwargs.get('kwargs', False)
        if self.kwarg:
            self.webhook_name_raw = self.kwarg.get('name', False)
            if not self.webhook_name_raw:
                self.webhook_name_raw = config().default_webhook_name
            self.webhook_name = self.webhook_dir_path.replace('/','.') + self.webhook_name_raw
            self.webhook_args = self.kwarg.get('args', False)

    def webhook_exec(self):
        try:
            module = importlib.import_module(self.webhook_name)
            run_whook = getattr(module, "run_webhook")
            np_payload = self.prepare_netpalm_payload()
            res = run_whook(netpalm_task_result=np_payload, kwargs=self.webhook_args)
            return res
        except Exception as e:
            return e

def exec_webhook_func(**kwargs):
    webhook = webhook_runner(kwargs=kwargs)
    execute = webhook.webhook_exec()
    return execute
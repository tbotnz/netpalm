from backend.core.confload.confload import config

import importlib

class webhook_runner:
    
    def __init__(self, webhook_name, webhook_args):
        self.webhook_dir_path = config().custom_webhooks
        if not webhook_name:
            self.webhook_name_raw = config().default_webhook_name
        self.webhook_name = self.webhook_dir_path.replace("/",".") + webhook_name
        self.webhook_args = webhook_args

    def webhook_exec(self,job_data):
        try:
            module = importlib.import_module(self.webhook_name)
            run_whook = getattr(module, "run_webhook")
            np_payload = job_data
            res = run_whook(netpalm_task_result=np_payload, netpalm_webhook_args=self.webhook_args)
            return res
        except Exception as e:
            return e

def exec_webhook_func(jobdata, webhook_payload):
    whook_name = webhook_payload.get("name", False)
    whook_args = webhook_payload.get("args", False)
    webhook = webhook_runner(webhook_name=whook_name, webhook_args=whook_args)
    execute = webhook.webhook_exec(job_data=jobdata)
    return execute

import requests

import json

from backend.plugins.utilities.jinja2.j2 import render_j2template
from backend.core.confload.confload import config

from backend.core.meta.rediz_meta import write_meta_error

from backend.core.models.service import model_service_template

import time

class service:
    
    def __init__(self):
        self.api_key = config.api_key
        self.netpalm_container_name = config.netpalm_container_name
        self.listen_port = config.listen_port
        self.self_api_call_timeout = config.self_api_call_timeout
        self.operation_mapping = {'create': 'setconfig', 'delete': 'setconfig', 'retrieve': 'getconfig', 'script': 'script'}

    def validate_template(self, template_name, **kwargs):
        try:
            kwarg = kwargs.get('kwargs', False)
            operation = kwarg.get("operation")
            args = kwarg.get("args")
            rendered_template = render_j2template(templat=template_name, template_type="service", kwargs=args)
            data = json.loads(rendered_template["data"]["task_result"]["template_render_result"])
            model_service_template(__root__=data)
            return data
        except Exception as e:
            write_meta_error(f"validate_template {e}")

    def execute_api_call(self,oper,payload):
        try:
            #update config to include https when finished webserver bundle
            headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
            }

            res = requests.post(f"http://{self.netpalm_container_name}:{self.listen_port}/{oper}", data=payload, timeout=self.self_api_call_timeout, headers=headers)
            if res.status_code == 201:
                return res.json()
            else:
                write_meta_error(f"error calling self api response {res.status_code}")
        except Exception as e:
            write_meta_error(f"execute_api_call service {e}")

    def execute_service(self,service, **kwargs):
        #loop through to the node layer
        kwarg = kwargs.get('kwargs', False)
        operation = kwarg.get("operation")
        args = kwarg.get("args")
        returrn_res = []
        for host in service:
            posted_operation = kwarg.get("operation", False)
            for operation in host["supported_methods"]:
                if operation["operation"] == posted_operation:
                    res = self.execute_api_call(oper=self.operation_mapping[posted_operation],payload=json.dumps(operation["payload"]))
                    time.sleep(1)
                    returrn_res.append({
                            "host": operation["payload"]["connection_args"]["host"],
                            "operation": posted_operation,
                            "data": res
                    })
        return returrn_res

def render_service(**kwargs):
    templat = kwargs.get("netpalm_service_name")
    exeservice = False
    try:
        s = service()
        res = s.validate_template(template_name=templat, kwargs=kwargs)
        exeservice = s.execute_service(service=res, kwargs=kwargs)
    except Exception as e:
        write_meta_error(f"render_service {e}")

    return exeservice
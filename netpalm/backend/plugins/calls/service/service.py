import logging

import json

import requests

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.utilities.rediz_meta import write_meta_error_string, write_mandatory_meta
from netpalm.backend.core.models.service import ServiceModelTemplate
from netpalm.backend.plugins.utilities.jinja2.j2 import render_j2template

log = logging.getLogger(__name__)


class service:

    def __init__(self, kw=None):
        self.api_key = config.api_key
        self.netpalm_container_name = config.netpalm_container_name
        self.listen_port = config.listen_port
        self.self_api_call_timeout = config.self_api_call_timeout
        self.operation_mapping = {
            "create": "/setconfig",
            "delete": "/setconfig",
            "retrieve": "/getconfig",
            "validate": "/getconfig",
            "script": "/script"
            }
        self.posted_kwargs = kw
        self.template_json = None

    def validate_template(self, template_name):
        try:
            args = self.posted_kwargs.get("args", None)
            # redner the j2 template
            rendered_template = render_j2template(
                templat=template_name,
                template_type="service",
                kwargs=args
                )
            # get the rendered data as json
            data = json.loads(
                rendered_template["data"]["task_result"]["template_render_result"]
                )
            # double check the template complies with the base model
            ServiceModelTemplate(__root__=data)
            self.template_json = data
            return True
        except Exception as e:
            write_meta_error_string(f"validate_template: {e}")
            log.error(f"validate_template: {e}")

    def execute_api_call(self, oper, payload):
        """API call handler for posting service subtasks"""
        try:
            # update config to include https when finished webserver bundle
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            # post to service api
            res = requests.post(
                f"{config.netpalm_callback_http_mode}://{self.netpalm_container_name}:{self.listen_port}{oper}",
                data=payload,
                timeout=self.self_api_call_timeout,
                headers=headers
                )
            if res.status_code == 201:
                return res.json()
            else:
                write_meta_error_string(
                    f"error calling self api response {res.status_code}"
                    )
        except Exception as e:
            write_meta_error_string(f"execute_api_call service: {e}")
            log.error(f"execute_api_call service: {e}")

    def execute_service(self):
        """Actions service template by distributing into subtasks"""
        posted_operation = self.posted_kwargs.get("operation")
        returrn_res = []
        nested_job_counter = 0
        # loop through the generated templates, actioning each
        for host in self.template_json:
            nested_job_counter += 1
            for operation in host["supported_methods"]:
                host_result = None
                # check for path param in template
                route_path = operation.get("path", False)
                if not route_path:
                    route_path = self.operation_mapping[posted_operation]
                if operation["operation"] == posted_operation:
                    # fire subtask call
                    res = self.execute_api_call(
                        oper=route_path,
                        payload=json.dumps(operation["payload"])
                        )
                    # prepare result
                    connection_args = operation["payload"].get("connection_args", False)
                    if connection_args:
                        host_result = connection_args["host"]
                    elif not connection_args:
                        host_result = f"nested_service_job_{nested_job_counter}"
                    # append result
                    returrn_res.append({
                        "host": host_result,
                        "operation": posted_operation,
                        "data": res
                        })
        return returrn_res


def render_service(**kwargs):
    """Main procedure for rendering and executing service & subtasks"""
    templat = kwargs.get("service_model")
    exeservice = None
    try:
        write_mandatory_meta()
        s = service(kw=kwargs)
        res = s.validate_template(template_name=templat)
        if res:
            exeservice = s.execute_service()
    except Exception as e:
        write_meta_error_string(f"render_service: {e}")

    return exeservice

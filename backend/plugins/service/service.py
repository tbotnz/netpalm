import requests

import json
import jsonschema

from backend.plugins.jinja2.j2 import render_j2template
from backend.core.confload.confload import config

class service:
    
    def __init__(self):
        self.api_key = config().apikey
        self.listen_ip = config().listen_ip
        self.listen_port = config().listen_port
        self.self_api_call_timeout = config().self_api_call_timeout
        self.operation_mapping = { 'create': 'setconfig', 'delete': 'setconfig', 'retrieve': 'getconfig' }
        self.service_schema = service = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "$id": "http://example.com/example.json",
        "type": "array",
        "title": "The Root Schema",
        "description": "The root schema comprises the entire JSON document.",
        "items": {
            "$id": "#/items",
            "type": "object",
            "title": "The Items Schema",
            "description": "An explanation about the purpose of this instance.",
            "default": {},
            "examples": [
                {
                    "supported_methods": [
                        {
                            "operation": "create",
                            "payload": {}
                        }
                    ]
                }
            ],
            "required": [
                "supported_methods"
            ],
            "properties": {
                "supported_methods": {
                    "$id": "#/items/properties/supported_methods",
                    "type": "array",
                    "title": "The Supported_methods Schema",
                    "description": "An explanation about the purpose of this instance.",
                    "default": [],
                    "items": {
                        "$id": "#/items/properties/supported_methods/items",
                        "type": "object",
                        "title": "The Items Schema",
                        "description": "An explanation about the purpose of this instance.",
                        "default": {},
                        "examples": [
                            {
                                "operation": "create",
                                "payload": {}
                            }
                        ],
                        "required": [
                            "operation",
                            "payload"
                        ],
                        "properties": {
                            "operation": {
                                "$id": "#/items/properties/supported_methods/items/properties/operation",
                                "type": "string",
                                "title": "The Operation Schema",
                                "description": "defines the purpose of the operation, eg create retrieve delete",
                                "default": "",
                                "examples": [
                                    "create",
                                    "update",
                                    "dete"
                                ]
                            },
                            "payload": {
                                "$id": "#/items/properties/supported_methods/items/properties/payload",
                                "type": "object",
                                "title": "The Payload Schema",
                                "description": "An explanation about the purpose of this instance.",
                                "default": {},
                                "examples": [
                                    {}
                                ]
                            }
                        }
                    }
                }
            }
        }
    }

    def validate_template(self, template_name, **kwargs):
        try:
            kwarg = kwargs.get('kwargs', False)
            operation = kwarg.get("operation")
            args = kwarg.get("args")
            rendered_template = render_j2template(templat=template_name, service=True, kwargs=args)
            data = json.loads(rendered_template["data"]["task_result"]["template_render_result"])
            jsonschema.validate(instance=data,schema=self.service_schema)
            return data
        except Exception as e:
            return str(e)

    def execute_api_call(self,oper,payload):
        try:
            #update config to include https when finished webserver bundle
            headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
            }
            if self.listen_ip == "0.0.0.0":
                ip = "127.0.0.1"
            else:
                ip = self.listen_ip

            res = requests.post("http://"+ip+":"+str(self.listen_port)+"/"+oper, data=payload, timeout=self.self_api_call_timeout, headers=headers)
            if res.status_code == 201:
                return res.json()
        except Exception as e:
            return str(e)

    def execute_service(self,service, **kwargs):
        #loop through to the node layer
        kwarg = kwargs.get('kwargs', False)
        operation = kwarg.get("operation")
        args = kwarg.get("args")
        returrn_res = {
                "data": [],
                "status": "success"
                }
        for host in service:
            posted_operation = kwarg.get("operation", False)
            for operation in host["supported_methods"]:
                if operation["operation"] == posted_operation:
                    res = self.execute_api_call(oper=self.operation_mapping[posted_operation],payload=json.dumps(operation["payload"]))
                    returrn_res["data"].append({
                            "host": operation["payload"]["connection_args"]["host"],
                            "operation": posted_operation,
                            "data": res
                    })
        return returrn_res

def render_service(templat, **kwargs):
    s = service()
    res = s.validate_template(template_name=templat, kwargs=kwargs["kwargs"])
    exeservice = s.execute_service(service=res, kwargs=kwargs["kwargs"])
    return exeservice
import base64
import os

from typing import Dict

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.models.task import ResponseBasic


class unvrsl:

    def __init__(self):
        self.routing_table = {
            "j2_config_templates": {"path": config.jinja2_config_templates, "extn": ".j2"},
            "python_service_templates": {"path": config.python_service_templates, "extn": ".py"},
            "j2_webhook_templates": {"path": config.webhook_jinja2_templates, "extn": ".j2"},
            "ttp_templates": {"path": config.ttp_templates, "extn": ".ttp"},
            "custom_scripts": {"path": config.custom_scripts, "extn": ".py"},
            "custom_webhooks": {"path": config.custom_webhooks, "extn": ".py"}
        }

    def add_template(self, payload: Dict[str, str]):
        try:
            raw_base = base64.b64decode(payload["base64_payload"]).decode('utf-8')
            template_path = self.routing_table[payload["route_type"]]["path"] + payload["name"] + self.routing_table[payload["route_type"]]["extn"]
            with open(template_path, "w") as file:
                file.write(raw_base)
            resultdata = ResponseBasic(status="success", data={"task_result": {"added": payload["name"]}}).dict()
            return resultdata
        except Exception as e:
            error = ResponseBasic(status="error", data={"task_result": {"error": str(e)}}).dict()
            return error

    def remove_template(self, payload: Dict[str, str]):
        try:
            template_path = self.routing_table[payload["route_type"]]["path"] + payload["name"] + self.routing_table[payload["route_type"]]["extn"]
            os.remove(template_path)
            resultdata = ResponseBasic(status="success", data={"task_result": {"removed": payload["name"]}}).dict()
            return resultdata
        except Exception as e:
            error = ResponseBasic(status="error", data={"task_result": {"error": str(e)}}).dict()
            return error

    def get_template(self, payload: Dict[str, str]):
        try:
            template_path = self.routing_table[payload["route_type"]]["path"] + payload["name"] + self.routing_table[payload["route_type"]]["extn"]
            result = None
            with open(template_path, "r") as file:
                result = file.read()
            raw_base = base64.b64encode(result.encode('utf-8'))
            resultdata = ResponseBasic(status="success", data={"task_result": {"base64_payload": raw_base}}).dict()
            return resultdata
        except Exception as e:
            error = ResponseBasic(status="error", data={"task_result": {"error": str(e)}}).dict()
            return error

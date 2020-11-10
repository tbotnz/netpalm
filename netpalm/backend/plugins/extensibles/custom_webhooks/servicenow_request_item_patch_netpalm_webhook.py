import json
import requests

import logging
from netpalm.backend.core.confload.confload import config

"""
netpalm webhook for updating a request item state and worknotes
IMPORTANT NOTES:
    webook requires a payload as per below
    "webhook": {
        "name": "servicenow_request_item_patch",
        "args": {
            "username": "admin",
            "password": "",
            "sys_id": "5d558ebf07679010430dff4c7c1ed036",
            "servicenow_instance": "dev98005.service-now.com"
        }
    }
"""

log = logging.getLogger(__name__)


def run_webhook(payload=False):
    try:
        if payload:
            log.info(f"run webhook: running servicenow webhook")
            # set variables for POST
            password = payload["webhook_args"]["password"]
            username = payload["webhook_args"]["username"]
            sys_id = payload["webhook_args"]["sys_id"]
            servicenow_instance = payload["webhook_args"]["servicenow_instance"]
            # generate clean payload for snow
            pl = {}
            if len(payload["data"]["task_errors"]) > 0:
                pl["state"] = "4"
            else:
                pl["state"] = "3"
            pl["work_notes"] = json.dumps(payload["data"]["task_result"], indent=3)
            # convert to json
            # Prepare requests data
            headers_val = config.default_webhook_headers
            verify_val = config.default_webhook_ssl_verify
            timeout_val = config.default_webhook_timeout
            # execute request
            response = requests.request("PATCH", url=f"https://{servicenow_instance}/api/now/table/sc_req_item/{sys_id}",
                                        headers=headers_val,
                                        verify=verify_val,
                                        timeout=timeout_val,
                                        json=pl,
                                        auth=(username, password)
                                        )
            if str(response.status_code)[:1] != "2":
                return False
            else:
                return True
        else:
            return False
    except Exception as e:
        log.error(f"run webhook: {e}")
        return e

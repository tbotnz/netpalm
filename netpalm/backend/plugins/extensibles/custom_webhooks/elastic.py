import json
import requests
import uuid

import logging
from netpalm.backend.core.confload.confload import config

from datetime import datetime
import re

"""
netpalm webhook for posting a document directly to an elasticsearch index
IMPORTANT NOTES:
    webook requires a payload as per below
    "webhook": {
        "name": "elastic",
        "args": {
            "username": "elastic",
            "password": "changeme",
            "index": "test",
            "elastic_instance": "http://127.0.0.1:9200"
        }
    }
"""

log = logging.getLogger(__name__)


def run_webhook(payload=False):
    try:
        if payload:
            log.info(f"run webhook: running elastic webhook")
            # set variables for POST
            password = payload["webhook_args"]["password"]
            username = payload["webhook_args"]["username"]
            index = payload["webhook_args"]["index"]
            elastic_instance = payload["webhook_args"]["elastic_instance"]
            del payload["webhook_args"]
            
            headers_val = config.default_webhook_headers
            verify_val = config.default_webhook_ssl_verify
            timeout_val = config.default_webhook_timeout

            payload = re.sub(r'\'(\d+)\'', r'\1', f"{payload}")
            payload = re.sub(r'\'(\d+)\'', r'\1', f"{payload}")

            # prepare time for elastic format
            now = datetime.now()
            time = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            timez = f"{time}Z"

            # append elastic attrs
            my_id = uuid.uuid4().hex
            
            payload["@version"] = 1
            payload["@timestamp"] = timez

            # execute request
            response = requests.request("POST", url=f"{elastic_instance}/{index}/{index}/{my_id}",
                                        headers=headers_val,
                                        verify=verify_val,
                                        timeout=timeout_val,
                                        json=payload,
                                        auth=(username, password)
                                        )
            if str(response.status_code)[:1] != "2":
                return False
            else:
                return True
        else:
            return False
    except Exception as e:
        log.error(f"elastic webhook: {e}")
        return e
import requests
import json

from backend.core.confload.confload import config

""" 
default webhook and boilerplate webhook template

IMPORTANT NOTES:
    - webhook function name must be "run_webhook"
    input params:
    - "netpalm_task_result" (dict)
    - **kwargs (dict)

"""
def run_webhook(payload=False):
    try:
        if payload:
            # convert to json    
            pl = json.dumps(payload)
            #prepare requests data
            url_val = config.default_webhook_url
            headers_val = config.default_webhook_headers
            verify_val = config.default_webhook_ssl_verify
            timeout_val = config.default_webhook_timeout
            pl = pl
            #execute request
            response = requests.request("POST", url=url_val, headers=headers_val, verify=verify_val, timeout=timeout_val, data=pl)
            if str(response.status_code)[:1] != "2":
                return False
            else:
                return True
        else:
            return False
    except Exception as e:
        return e
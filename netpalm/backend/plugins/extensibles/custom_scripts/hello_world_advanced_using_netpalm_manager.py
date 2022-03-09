from netpalm.backend.core.manager.netpalm_manager import NetpalmManager

import logging

# all functions need to be wrapped in the "run" function and pass in kwargs
# JSON example to send into the /script route is as below
#
# {
# 	"script": "hello_world_advanced_using_netpalm_manager",
# 	"args": {
# 		"host": "10.0.2.33",
#         "username": "admin",
#         "password": "admin"
# 	},
# 	"queue_strategy": "fifo"
# }
#

log = logging.getLogger(__name__)


def run(**kwargs):
    try:
        # mandatory get of kwargs - payload comes through as {"kwargs": {"host": "10.0.2.33", "username": "admin", "password": "admin"}}
        args = kwargs.get("kwargs")
        # access your passed in vars here in a dict format - payload is now {"host": "10.0.2.33", "username": "admin", "password": "admin"}
        username = args["username"]
        password = args["password"]
        host = args["host"]

        log.info(f"hello_world_advanced_using_netpalm_manager: recieved {args}")

        # we will now use the netpalm manager to interface with netpalm
        # this section shows how to prepare a payload to send into netpalm
        netmiko_send_data = {
            "library": "netmiko",
            "connection_args": {
                "device_type": "cisco_ios",
                "host": host,
                "username": username,
                "password": password,
                "timeout": 5
            },
            "command": "show run | i hostname",
            "queue_strategy": "pinned"
        }
        mgr = NetpalmManager()
        job_result = mgr.get_config_netmiko(netmiko_send_data)
        return_result = mgr.retrieve_task_result(job_result)

        log.info(f"hello_world_advanced_using_netpalm_manager: got back from task {return_result}")

        # we can also trigger webhooks from within the script if required using the manager as below
        # webhooks can also be triggered outside of the script by simply using the webhook key against the REST API
        webhook_meta = {
            "name": "default_webhook",
            "args": {
                "insert": "something useful"
            }
        }

        log.info(f"hello_world_advanced_using_netpalm_manager: triggering webhook with {webhook_meta}")

        mgr.trigger_webhook(webhook_meta_data=webhook_meta, webhook_payload=return_result)

        if return_result["data"]["task_result"]:
            if "bufoon" in return_result["data"]["task_result"]:
                return "MeowCat"
            else:
                return "MeowMeow"
        else:
            return "MeowMeow"

    except KeyError as e:
        raise Exception(f"Required args: {e}")
    except Exception as e:
        raise Exception(e)

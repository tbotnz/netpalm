from netpalm.backend.core.manager.netpalm_manager import NetpalmManager

# all functions need to be wrapped in the "run" function and pass in kwargs
# JSON example to send into the /script route is as below
#
# {
# 	"script":"hello_world",
# 	"args":{
# 		"hello":"world"
# 	}
# }
#
def run(**kwargs):
    try:
        # mandatory get of kwargs - payload comes through as {"kwargs": {"hello": "world"}}
        args = kwargs.get("kwargs")
        # access your vars here in a dict format - payload is now {"hello": "world"}
        world = args["hello"]
        # reutn "world"
        netmiko_send_data = {
            "library": "netmiko",
            "connection_args": {
                "device_type": "cisco_ios",
                "host": "10.0.2.33",
                "username": "admin",
                "password": "admin",
                "timeout": 5
            },
            "command": "show run | i hostname",
            "queue_strategy": "pinned"
        }
        mgr = NetpalmManager()
        job_result = mgr.get_config_netmiko(netmiko_send_data)
        return_result = mgr.retrieve_task_result(job_result)
        return return_result
    except KeyError as e:
        raise Exception(f"Required args: {e}")
    except Exception as e:
        raise Exception(e)

import logging

from pydantic import BaseModel
from netpalm.backend.plugins.calls.service.netpalmservice import NetpalmService
from netpalm.backend.core.manager.netpalm_manager import NetpalmManager

log = logging.getLogger(__name__)


class NetpalmUserServiceModel(BaseModel):
    hostname: str


class NetpalmUserService(NetpalmService):

    mgr = NetpalmManager()
    model = NetpalmUserServiceModel

    def create(self, model_data: model):
        log.info(f"netpalm service: made it with your {model_data.hostname}!")
        log.info(f"netpalm service: service created {self.service_id}!")

        netmiko_send_data = {
            "library": "netmiko",
            "connection_args": {
                "device_type": "cisco_ios",
                "host": model_data.hostname,
                "username": "admin",
                "password": "admin",
                "timeout": 5
            },
            "command": "show run | i hostname",
            "queue_strategy": "pinned"
        }
        job_result = self.mgr.get_config_netmiko(netmiko_send_data)
        return_result = self.mgr.retrieve_task_result(job_result)
        self.mgr.set_service_instance_status(self.service_id, state="errored")
        return return_result

    def update(self, model: model):
        log.info(f"netpalm service: update method not implemented on your service")
        pass

    def delete(self, model: model):
        log.info(f"netpalm service: delete method not implemented on your service")
        pass

    def re_deploy(self, model: model):
        log.info(f"netpalm service: re_deploy method not implemented on your service")
        pass

    def validate(self, model: model):
        log.info(f"netpalm service: validate method not implemented on your service")
        pass

    def health_check(self, model: model):
        log.info(f"netpalm service: health_check method not implemented on your service")
        pass


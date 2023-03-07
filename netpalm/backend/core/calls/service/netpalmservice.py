import logging

from pydantic import BaseModel

from netpalm.backend.core.confload.confload import config

log = logging.getLogger(__name__)


class NetpalmService:
    def __init__(self, model, service_id=None):
        log.info(f"netpalm service: invoking")
        self.model = model
        self.service_id = service_id

    def create(self):
        log.info(f"netpalm service: create method not implemented on your service")
        pass

    def update(self):
        log.info(f"netpalm service: update method not implemented on your service")
        pass

    def delete(self):
        log.info(f"netpalm service: delete method not implemented on your service")
        pass

    def re_deploy(self):
        log.info(f"netpalm service: re_deploy method not implemented on your service")
        pass

    def validate(self):
        log.info(f"netpalm service: validate method not implemented on your service")
        pass

    def health_check(self):
        log.info(
            f"netpalm service: health_check method not implemented on your service"
        )
        pass

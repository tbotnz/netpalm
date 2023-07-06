import logging


from pymongo import MongoClient, database
from netpalm.backend.core.confload.confload import config, Config

from netpalm.backend.core.utilities.rediz_meta import (
    render_netpalm_payload,
)

log = logging.getLogger(__name__)


def write_task_result(result_payload):
    payload = render_netpalm_payload(job_result=result_payload)
    try:
        if config.mongo_user:
            raw_connection = MongoClient(
                host=config.mongo_server_ip,
                port=config.mongo_server_port,
                username=config.mongo_user,
                password=config.mongo_password,
            )
        else:
            raw_connection = MongoClient(
                host=config.mongo_server_ip,
                port=config.mongo_server_port,
            )

        base_connection = raw_connection.netpalm
        base_connection["task_results"].insert_one(payload)
    except Exception as e:
        log.error(f"failed to write task result to mongo: {e}")
        return False
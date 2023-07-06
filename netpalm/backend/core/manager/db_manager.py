import logging

from netpalm.backend.core.confload.confload import config, Config

from netpalm.backend.core.redis.rediz import Rediz
from netpalm.backend.core.mongo.mongdb import MongDB

from fastapi.encoders import jsonable_encoder

log = logging.getLogger(__name__)


class DBManager:
    def __init__(self):
        self.redis = Rediz()
        self.mongo = MongDB()

    def execute_task(self, method, **kwargs):
        """main entry point for rpc tasks"""
        kw = kwargs.get("kwargs", False)
        connectionargs = kw.get("connection_args", False)
        host = False
        if connectionargs:
            host = kw["connection_args"].get("host", False)
        queue_strategy = kw.get("queue_strategy", False)
        if queue_strategy == "pinned":
            self.redis.reoute_and_create_q_worker(hst=host)
            r = self.redis.sendtask(q=host, exe=method, kwargs=kw)
        else:
            r = self.redis.sendtask(q=config.redis_fifo_q, exe=method, kwargs=kw)
        log.debug(f"Task sent to redis: {r}")

        self.mongo.insert(data=jsonable_encoder(r), collection="tasks")
        return r
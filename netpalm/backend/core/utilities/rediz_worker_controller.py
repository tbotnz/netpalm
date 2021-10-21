from redis import Redis
from rq import Queue, Connection, Worker
import socket
import json
import logging
import uuid

from netpalm.backend.core.confload.confload import config, Config
from netpalm.backend.core.models.models import PinnedStore

log = logging.getLogger(__name__)


class WorkerRediz:
    def __init__(self, config: Config = config):

        # globals
        self.server = config.redis_server
        self.port = config.redis_port
        self.key = config.redis_key
        self.ttl = config.redis_task_ttl
        self.timeout = config.redis_task_timeout
        self.task_result_ttl = config.redis_task_result_ttl
        self.core_q = config.redis_core_q
        # config check if TLS required
        if config.redis_tls_enabled:
            self.base_connection = Redis(
                host=self.server,
                port=self.port,
                password=self.key,
                ssl=True,
                ssl_cert_reqs="required",
                ssl_keyfile=config.redis_tls_key_file,
                ssl_certfile=config.redis_tls_cert_file,
                ssl_ca_certs=config.redis_tls_ca_cert_file,
                socket_connect_timeout=config.redis_socket_connect_timeout,
                socket_keepalive=config.redis_socket_keepalive,
            )
        else:
            self.base_connection = Redis(
                host=self.server,
                port=self.port,
                password=self.key,
                socket_connect_timeout=config.redis_socket_connect_timeout,
                socket_keepalive=config.redis_socket_keepalive,
            )

    def process_worker_listen(self):
        """pinned worker master container process"""
        with Connection(self.base_connection):
            # register container to pinned store
            r = self.base_connection.get(config.redis_pinned_store)
            rjson = json.loads(r)
            hstname = socket.gethostname()
            listn_queue = f"{hstname}_processworker"
            log.info(rjson)
            data = PinnedStore(
                hostname=f"{hstname}",
                count=0,
                limit=config.pinned_process_per_node,
                pinned_listen_queue=listn_queue,
            ).dict()
            rjson.append(data)
            log.info(rjson)
            self.base_connection.set(config.redis_pinned_store, json.dumps(rjson))
            # setup queue and start working
            q = Queue(listn_queue)
            u_uid = uuid.uuid4()
            worker_name = f"{listn_queue}_{u_uid}"
            worker = Worker(q, name=worker_name)
            worker.work()

    def pinned_worker_listen(self, queue):
        """pinned worker instance process"""
        with Connection(self.base_connection):
            # update pinned db
            r = self.base_connection.get(config.redis_pinned_store)
            rjson = json.loads(r)
            hstname = socket.gethostname()
            for container in rjson:
                if container["hostname"] == f"{hstname}":
                    container["count"] += 1
                    break
            self.base_connection.set(config.redis_pinned_store, json.dumps(rjson))
            # setup queue and start working
            q = Queue(queue)
            u_uid = uuid.uuid4()
            worker_name = f"{queue}_{u_uid}"
            worker = Worker(q, name=worker_name)
            worker.work()

    def fifo_worker_listen(self, queue, counter):
        """fifo worker instance process"""
        with Connection(self.base_connection):
            q = Queue(queue)
            u_uid = uuid.uuid4()
            worker_name = f"{queue}_{counter}_{u_uid}"
            worker = Worker(q, name=worker_name)
            worker.work()

    def worker_cleanup(self):
        """cleans up jobs on container shutdown """
        # clear the pinned db store for capacity mgmt
        r = self.base_connection.get(config.redis_pinned_store)
        rjson = json.loads(r)
        idex = 0
        hstname = socket.gethostname()
        for container in rjson:
            if container["hostname"] == f"{hstname}":
                rjson.pop(idex)
                self.base_connection.set(config.redis_pinned_store, json.dumps(rjson))
                break
            idex += 1
        # purge all workers still running on this container
        workers = Worker.all(connection=self.base_connection)
        for worker in workers:
            if worker.hostname == f"{hstname}":
                worker.register_death()

    def pub_sub(self):
        result = self.base_connection.pubsub()
        return result

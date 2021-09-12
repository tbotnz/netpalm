from redis import Redis
from rq import Queue, Connection, Worker
import socket
import json
import logging
import uuid

from netpalm.backend.core.confload.confload import Config
from netpalm.backend.core.models.models import PinnedStore

log = logging.getLogger(__name__)


class RedisWorker:
    def __init__(self, config: Config):

        # globals
        self.server = config.redis_server
        self.port = config.redis_port
        self.key = config.redis_key
        self.ttl = config.redis_task_ttl
        self.timeout = config.redis_task_timeout
        self.task_result_ttl = config.redis_task_result_ttl
        self.core_q = config.redis_core_q

        self.redis_pinned_store = config.redis_pinned_store
        self.pinned_process_per_node = config.pinned_process_per_node

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

        self.worker_name_base = ""
        self._uuid = uuid.uuid4()

    def worker_cleanup(self):
        """cleans up jobs on container shutdown """
        # clear the pinned db store for capacity mgmt
        r = self.base_connection.get(self.redis_pinned_store)
        rjson = json.loads(r)
        idex = 0
        hstname = socket.gethostname()
        for container in rjson:
            if container["hostname"] == f"{hstname}":
                rjson.pop(idex)
                self.base_connection.set(self.redis_pinned_store, json.dumps(rjson))
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

    @property
    def worker_name(self):
        return f"{self.worker_name_base}_{self._uuid}"

    def _listen(self, queue_name):
        queue = Queue(queue_name)
        worker = Worker(queue, name=self.worker_name)
        worker.work()


class RedisFifoWorker(RedisWorker):
    def __init__(self, config: Config, queue_name: str, counter: int):
        super().__init__(config)
        self.queue_name = queue_name
        self.worker_name_base = f"{queue_name}_{counter}"

    def listen(self):
        """fifo worker instance process"""
        with Connection(self.base_connection):
            self._listen(self.queue_name)


class RedisPinnedWorker(RedisWorker):
    def __init__(self, config: Config, queue_name: str):
        super().__init__(config)
        self.queue_name = queue_name
        self.worker_name_base = queue_name

    def listen(self):
        """pinned worker instance process"""
        with Connection(self.base_connection):
            # update pinned db
            r = self.base_connection.get(self.redis_pinned_store)
            rjson = json.loads(r)
            hostname = socket.gethostname()
            for container in rjson:
                if container["hostname"] == hostname:
                    container["count"] += 1
                    break
            self.base_connection.set(self.redis_pinned_store, json.dumps(rjson))

            self._listen(self.queue_name)


class RedisProcessWorker(RedisWorker):
    def __init__(self, config: Config):
        super().__init__(config)
        self.hostname = socket.gethostname()
        self.queue_name = f"{self.hostname}_processworker"
        self.worker_name_base = self.queue_name

    def listen(self):
        """pinned worker master container process"""
        with Connection(self.base_connection):
            # register container to pinned store
            r = self.base_connection.get(self.redis_pinned_store)
            rjson = json.loads(r)
            log.info(rjson)
            data = PinnedStore(
                hostname=self.hostname,
                count=0,
                limit=self.pinned_process_per_node,
                pinned_listen_queue=self.queue_name
            ).dict()
            rjson.append(data)
            log.info(rjson)
            self.base_connection.set(self.redis_pinned_store, json.dumps(rjson))
            # setup queue and start working

            self._listen(self.queue_name)

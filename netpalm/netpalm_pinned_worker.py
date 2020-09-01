import logging
import uuid
from multiprocessing import Process

from redis import Redis
from rq import Queue, Connection, Worker

from .backend.core.confload.confload import config
from .netpalm_worker_common import start_broadcast_listener_process

config.setup_logging(max_debug=True)
log = logging.getLogger(__name__)


# process listner
def start_processworkerprocess():
    p = Process(target=processworker)
    p.start()


def we_are_controller():
    import sys
    for part in sys.argv:
        if 'controller' in part:
            log.error(f'{sys.argv}')
            return True
    return False


# listens on the core queue for messages from the controller, used to create new processes on demand as needed
def processworker():
    if not we_are_controller():
        start_broadcast_listener_process()
        try:
            if config.redis_tls_enabled:
                base_connection = Redis(
                                        host=config.redis_server,
                                        port=config.redis_port,
                                        password=config.redis_key,
                                        ssl=True,
                                        ssl_cert_reqs='required',
                                        ssl_keyfile=config.redis_tls_key_file,
                                        ssl_certfile=config.redis_tls_cert_file,
                                        ssl_ca_certs=config.redis_tls_ca_cert_file,
                                        socket_connect_timeout=config.redis_socket_connect_timeout,
                                        socket_keepalive=config.redis_socket_keepalive
                                        )
            else:
                base_connection = Redis(
                                        host=config.redis_server,
                                        port=config.redis_port,
                                        password=config.redis_key,
                                        socket_connect_timeout=config.redis_socket_connect_timeout,
                                        socket_keepalive=config.redis_socket_keepalive
                )
            with Connection(base_connection):
                q = Queue(config.redis_core_q)
                u_uid = uuid.uuid4()
                worker_name = f"{config.redis_core_q}_{u_uid}"
                worker = Worker(q, name=worker_name)
                worker.work()
        except Exception as e:
            return e


def pinned_worker(queue):
    try:
        if config.redis_tls_enabled:
            base_connection = Redis(
                                    host=config.redis_server,
                                    port=config.redis_port,
                                    password=config.redis_key,
                                    ssl=True,
                                    ssl_cert_reqs='required',
                                    ssl_keyfile=config.redis_tls_key_file,
                                    ssl_certfile=config.redis_tls_cert_file,
                                    ssl_ca_certs=config.redis_tls_ca_cert_file,
                                    socket_connect_timeout=config.redis_socket_connect_timeout,
                                    socket_keepalive=config.redis_socket_keepalive
                                    )
        else:
            base_connection = Redis(
                                    host=config.redis_server,
                                    port=config.redis_port,
                                    password=config.redis_key,
                                    socket_connect_timeout=config.redis_socket_connect_timeout,
                                    socket_keepalive=config.redis_socket_keepalive
                                    )
        with Connection(base_connection):
            q = Queue(queue)
            u_uid = uuid.uuid4()
            worker_name = f"{queue}_{u_uid}"
            worker = Worker(q, name=worker_name)
            worker.work()
    except Exception as e:
        return e


def pinned_worker_constructor(queue):
    p = Process(target=pinned_worker, args=(queue,))
    p.start()


if __name__ == '__main__':
    start_processworkerprocess()

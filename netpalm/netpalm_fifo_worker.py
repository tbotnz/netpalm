import uuid
from multiprocessing import Process

from redis import Redis
from rq import Queue, Connection, Worker

from .backend.core.confload.confload import config
from .netpalm_worker_common import start_broadcast_listener_process

config.setup_logging(max_debug=True)


def fifo_worker(queue, counter):
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
            worker_name = f"{queue}_{counter}_{u_uid}"
            worker = Worker(q, name=worker_name)
            worker.work()
    except Exception as e:
        return e

def fifo_worker_constructor(queue):
    start_broadcast_listener_process()
    for i in range(config.fifo_process_per_node):
        p = Process(target=fifo_worker, args=(queue,i,))
        p.start()

def start_worker():
    fifo_worker_constructor(config.redis_fifo_q)

from multiprocessing import Process

from redis import Redis
from rq import Queue, Connection, Worker

from backend.core.confload.confload import config
from netpalm_worker_common import start_broadcast_listener_process

config.setup_logging()


def fifo_worker(queue):
    try:
        with Connection(Redis(host=config.redis_server, port=config.redis_port, password=config.redis_key)):
            q = Queue(queue)
            worker = Worker(q)
            worker.work()
    except Exception as e:
        return e

def fifo_worker_constructor(queue):
    start_broadcast_listener_process()
    for i in range(config.fifo_process_per_node):
        p = Process(target=fifo_worker, args=(queue,))
        p.start()

fifo_worker_constructor(config.redis_fifo_q)

from multiprocessing import Process
import time
import sys

from .backend.core.confload.confload import config
from .netpalm_worker_common import start_broadcast_listener_process
from .backend.core.utilities.rediz_worker_controller import RedisWorker, RedisFifoWorker

config.setup_logging(max_debug=True)


def fifo_worker(queue, counter):
    try:
        wr = RedisFifoWorker(config, queue, counter)
        wr.listen()
    except Exception as e:
        return e


def fifo_worker_constructor(queue):
    try:
        start_broadcast_listener_process()
        for i in range(config.fifo_process_per_node):
            p = Process(target=fifo_worker, args=(queue, i,))
            p.start()
        while True:
            time.sleep(99999999)
    finally:
        cleanup = RedisWorker(config)
        cleanup.worker_cleanup()
        sys.exit()


def start_worker():
    fifo_worker_constructor(config.redis_fifo_q)

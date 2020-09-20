import uuid
from multiprocessing import Process
import time
import socket
import json
import sys

from redis import Redis
from rq import Queue, Connection, Worker

from .backend.core.confload.confload import config
from .netpalm_worker_common import start_broadcast_listener_process
from .backend.core.utilities.rediz_worker_controller import WorkerRediz

config.setup_logging(max_debug=True)


def fifo_worker(queue, counter):
    try:
        wr = WorkerRediz()
        wr.fifo_worker_listen(queue, counter)
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
        cleanup = WorkerRediz()
        cleanup.worker_cleanup()
        sys.exit()


def start_worker():
    fifo_worker_constructor(config.redis_fifo_q)

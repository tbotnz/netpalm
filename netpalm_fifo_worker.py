from redis import Redis
import redis
from rq import Queue, Connection, Worker
from rq.job import Job
import json
from multiprocessing import Process

from backend.core.confload.confload import config

def fifo_worker(queue):
    try:
        with Connection(Redis(host=config().redis_server,port=config().redis_port,password=config().redis_key)):
            q = Queue(queue)
            worker = Worker(q)
            worker.work()
    except Exception as e:
        return e

def fifo_worker_constructor(queue):
    for i in range(config().fifo_process_per_node):
        p = Process(target=fifo_worker, args=(queue,))
        p.start()

fifo_worker_constructor(config().redis_fifo_q)
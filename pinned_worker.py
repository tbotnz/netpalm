from redis import Redis
import redis
from rq import Queue, Connection, Worker
from rq.job import Job
import json
from multiprocessing import Process

from backend.core.confload.confload import config

#process listner
def processworkerprocess():
    p = Process(target=processworker)
    p.start()

#used to create a queue for establish processes
def processworker():
    try:
        with Connection(Redis(config().redis_server,config().redis_port)):
            q = Queue(config().redis_core_q)
            worker = Worker(q)
            worker.work()
    except Exception as e:
        return e

def pinned_worker(queue):
    try:
        with Connection(Redis(config().redis_server,config().redis_port)):
            q = Queue(queue)
            worker = Worker(q)
            worker.work()
    except Exception as e:
        return e

def pinned_worker_constructor(queue):
    for i in range(config().pinned_process_per_node):
        p = Process(target=pinned_worker, args=(queue,))
        p.start()

processworkerprocess()

from redis import Redis
import redis
from rq import Queue, Connection, Worker
from rq.job import Job
import json
from multiprocessing import Process

#load config
from backend.core.confload.confload import config

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

#creates a process for an individual device
def nodeworker(queue):
    try:
        with Connection(Redis(config().redis_server,config().redis_port)):
            q = Queue(queue)
            worker = Worker(q)
            worker.work()
    except Exception as e:
        return e

def nodeworkerconstructor(queue):
    p = Process(target=nodeworker, args=(queue,))
    p.start()


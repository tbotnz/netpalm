import logging
from multiprocessing import Process

from redis import Redis
from rq import Queue, Connection, Worker

from backend.core.confload.confload import config
from netpalm_worker_common import start_broadcast_listener_process

config.setup_logging()
log = logging.getLogger(__name__)

# process listner
def processworkerprocess():
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
            with Connection(Redis(host=config.redis_server, port=config.redis_port, password=config.redis_key)):
                q = Queue(config.redis_core_q)
                worker = Worker(q)
                worker.work()
        except Exception as e:
            return e


def pinned_worker(queue):
    try:
        with Connection(Redis(host=config.redis_server,port=config.redis_port,password=config.redis_key)):
            q = Queue(queue)
            worker = Worker(q)
            worker.work()
    except Exception as e:
        return e

def pinned_worker_constructor(queue):
    p = Process(target=pinned_worker, args=(queue,))
    p.start()

if __name__ == '__main__':
    processworkerprocess()

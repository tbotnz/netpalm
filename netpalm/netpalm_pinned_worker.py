import logging
from multiprocessing import Process
import sys
import time

from .backend.core.confload.confload import config
from .netpalm_worker_common import start_broadcast_listener_process
from .backend.core.utilities.rediz_worker_controller import RedisWorker, RedisPinnedWorker, RedisProcessWorker

config.setup_logging(max_debug=True)
log = logging.getLogger(__name__)


def start_processworkerprocess():
    try:
        """process to run the processworker core function"""
        p = Process(target=processworker)
        p.start()
        while True:
            time.sleep(99999999)
    finally:
        cleanup = RedisWorker(config)
        cleanup.worker_cleanup()
        sys.exit()


def we_are_controller():
    import sys
    for part in sys.argv:
        if 'controller' in part:
            return True
    return False


def processworker():
    """
        listens on the core queue for messages from the controller,
        single processesworker runs per controller.
        used to create new processes on demand as needed
    """
    if not we_are_controller():
        start_broadcast_listener_process()
        wr = RedisProcessWorker(config)
        wr.listen()


def pinned_worker(queue):
    try:
        wr = RedisPinnedWorker(config, queue)
        wr.listen()
    except Exception as e:
        return e


def pinned_worker_constructor(queue):
    """process constructor to run the pinned_worker"""
    p = Process(target=pinned_worker, args=(queue,))
    p.start()


if __name__ == '__main__':
    start_processworkerprocess()

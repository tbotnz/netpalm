import os
import signal
import socket
import logging

log = logging.getLogger(__name__)


def kill_worker_pid(**kwargs):
    """kills a rq worker process by its pid"""
    try:
        hostname = kwargs.get("hostname")
        pid = kwargs.get("pid")
        output = socket.gethostname()
        if f"{output}" == hostname:
            log.info({f"kill_worker_pid: killing worker PID {pid} on {output}"})
            os.kill(int(pid), signal.SIGINT)
    except Exception as e:
        log.error({f"kill_worker_pid: {e}"})
        return e

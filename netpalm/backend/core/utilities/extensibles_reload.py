import logging

import os, signal

log = logging.getLogger(__name__)

def reload_extensibles_func():
    try:
        with open("controller.pid", encoding = 'utf-8') as f:
            pid = f.readline()
            log.info(f"reload_extensibles: reloading extensibles for {pid}")
            os.kill(int(pid), signal.SIGHUP)
            return True
    except FileNotFoundError:
        return False
    except Exception as e:
        log.error(f"reload_extensibles: reloading extensibles for {e}")
        return False
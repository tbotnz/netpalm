import json
import logging

log = logging.getLogger(__name__)
DEFAULTS_FILENAME = "/code/config/defaults.json"
CONFIG_FILENAME = "/code/config/config.json"


def load_config_files(defaults_filename: str = DEFAULTS_FILENAME, config_filename: str = CONFIG_FILENAME) -> dict:
    data = {}

    for fname in (defaults_filename, config_filename):
        try:
            with open(fname) as infil:
                data.update(json.load(infil))
        except FileNotFoundError:
            log.warning(f"Couldn't find {fname}")

    if not data:
        raise RuntimeError(f"Could not find either {defaults_filename} or {config_filename}")

    return data


data = load_config_files()

bind = data["listen_ip"] + ":" + str(data["listen_port"])
workers = data["gunicorn_workers"]
timeout = 3 * 60
keepalive = 24 * 60 * 60
worker_class = "uvicorn.workers.UvicornWorker"
threads = 45

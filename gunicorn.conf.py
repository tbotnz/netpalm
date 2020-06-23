import os
import json
import multiprocessing

with open("/code/config.json") as json_file:
    data = json.load(json_file)

bind = data["listen_ip"] +':'+str(data["listen_port"])
#bind = "0.0.0.0:9000"
workers = data["gunicorn_workers"]
timeout = 3 * 60  # 3 minutes
keepalive = 24 * 60 * 60  # 1 day
worker_class = "gthread"
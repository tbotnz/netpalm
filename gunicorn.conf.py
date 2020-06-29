import os
import json
import multiprocessing

with open("/code/config.json") as json_file:
    data = json.load(json_file)

bind = data["listen_ip"] +':'+str(data["listen_port"])
workers = data["gunicorn_workers"]
timeout = 3 * 60
keepalive = 24 * 60 * 60
worker_class = "uvicorn.workers.UvicornWorker"
threads = 45

from netpalm.backend.core.confload.confload import get_settings

settings = get_settings()

bind = settings.listen_ip + ":" + str(settings.listen_port)
workers = settings.gunicorn_workers
timeout = 3 * 60
keepalive = 24 * 60 * 60
worker_class = "uvicorn.workers.UvicornWorker"
threads = 45

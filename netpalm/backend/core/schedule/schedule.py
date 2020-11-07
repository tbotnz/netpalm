import logging
import uuid
import datetime
import requests
import json
from jsonpath_ng import jsonpath, parse

from fastapi.exceptions import HTTPException

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.models.task import ResponseBasic

log = logging.getLogger(__name__)


def execute_api_call(**kwargs):
    """API call handler for posting subtasks"""
    try:
        # update config to include https when finished webserver bundle
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json"
        }
        path = kwargs.get("path", None)
        payload = kwargs.get("payload", None)
        # post to service api
        r = requests.post(
            url=f"{config.netpalm_callback_http_mode}://{config.netpalm_container_name}:{config.listen_port}{path}",
            json=payload,
            timeout=config.self_api_call_timeout,
            headers=headers
            )
        if r.status_code == 201:
            return r.json()
        else:
            log.error(f"execute_api_call: {r.text}")
    except Exception as e:
        log.error(f"execute_api_call: {e}")


class Schedulr:

    def __init__(self):
        if config.redis_tls_enabled:
            self.connect_args = {
                "host": config.redis_server,
                "port": config.redis_port,
                "password": config.redis_key,
                "ssl": True,
                "ssl_cert_reqs": "required",
                "ssl_keyfile": config.redis_tls_key_file,
                "ssl_certfile": config.redis_tls_cert_file,
                "ssl_ca_certs": config.redis_tls_ca_cert_file,
                "socket_connect_timeout": config.redis_socket_connect_timeout,
                "socket_keepalive": config.redis_socket_keepalive
            }
        else:
            self.connect_args = {
                "host": config.redis_server,
                "port": config.redis_port,
                "password": config.redis_key,
                "socket_connect_timeout": config.redis_socket_connect_timeout,
                "socket_keepalive": config.redis_socket_keepalive
            }
        self.scheduler = None

    def init_scheduler(self):
        self.jobstores = {
            "default": RedisJobStore(
                                jobs_key=config.redis_schedule_store,
                                run_times_key=config.redis_schedule_store_stats,
                                **self.connect_args
                                )
        }
        self.executors = {
            "default": ThreadPoolExecutor(config.apscheduler_num_threads),
            "processpool": ProcessPoolExecutor(config.apscheduler_num_processes)
        }
        job_defaults = {
            "coalesce": False
        }
        self.scheduler = scheduler = BackgroundScheduler(
                                    jobstores=self.jobstores,
                                    executors=self.executors,
                                    job_defaults=job_defaults
                                    )
        scheduler.start()

    def purge_creds(self, kw):
        """ purge creds from any redis payload """
        try:
            json_scrub_dict = ["$.payload.connection_args.username", "$.payload.connection_args.password"]
            for scrub_match in json_scrub_dict:
                jsonpath_expr = parse(scrub_match)
                jsonpath_expr.find(kw)
                jsonpath_expr.update(kw, "*******")
            return kw
        except Exception as e:
            log.error(f"purge_creds: {e}")

    def get_scheduled_jobs(self):
        result = []
        result_data = False
        res = self.scheduler.get_jobs(jobstore="default")
        if res:
            for r in res:
                kwar = self.purge_creds(kw=r.kwargs)
                result.append(
                                {
                                    "name": r.name,
                                    "id": r.id,
                                    "trigger": f"{r.trigger}",
                                    "next_run_time": f"{r.next_run_time}",
                                    "payload": kwar
                                }
                            )
        result_data = ResponseBasic(status="success", data={
            "task_result": {"scheduled_tasks": result}
            }).dict()
        return result_data

    def add_netpalm_job(self, input_payload, job_name, trigger, trigger_args):
        try:
            random_job_id = uuid.uuid4()
            job_id = f"{random_job_id}_{job_name}"
            self.scheduler.add_job(
                                execute_api_call,
                                kwargs=input_payload,
                                name=job_id,
                                trigger=trigger,
                                **trigger_args
                                )
        except Exception as e:
            log.error(f"add_netpalm_job: {e}")

    def remove_job(self, job_id):
        self.scheduler.remove_job(job_id)

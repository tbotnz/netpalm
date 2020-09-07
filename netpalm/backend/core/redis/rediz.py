import datetime
import json
import logging
from typing import Union, Dict, List

from jsonpath_ng import jsonpath, parse

import redis_lock
from cachelib import RedisCache

import uuid

from redis import Redis
from rq import Queue, Worker
from rq.job import Job
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

from netpalm.backend.core.confload.confload import config, Config
from netpalm.backend.core.models.task import Response, WorkerResponse
from netpalm.backend.core.models.service import ServiceModel
from netpalm.backend.core.models.transaction_log import TransactionLogEntryModel, TransactionLogEntryType
from netpalm.backend.core.routes import routes

log = logging.getLogger(__name__)


class ClearableCache(RedisCache):
    def keys(self, key_pattern: str = ""):
        prefix = f"{self.key_prefix}{key_pattern}*"
        keys = self._client.keys(prefix)
        return keys

    def clear_keys(self, key_pattern: str):
        if not key_pattern:
            raise ValueError(f"no key_pattern provided!")

        status = False
        keys = self.keys(key_pattern)
        if keys:
            status = self._client.delete(*keys)

        return status


class DisabledCache:
    @staticmethod
    def always_return_none(*args, **kwargs):
        return None

    def __getattr__(self, item):
        return self.always_return_none


class ExtnUpdateLog:
    """Class for managing the Extensibles Update Log"""

    def __init__(self, base_connection: Redis, log_name: str, create=True):
        self.base_connection = base_connection
        self.log_name = log_name
        # scope of this lock is to prevent more than one controller from changing log at once
        self.lock = redis_lock.Lock(base_connection, config.redis_update_log,
                                    expire=30, auto_renewal=True)  # lock should only expire if a process dies
        self.initialize_record = {
            "type": TransactionLogEntryType.init,
            "data": {"init": True}
        }
        if create:
            self.create(strict=False)

    def clear(self):
        with self.lock:
            return self.base_connection.delete(self.log_name)

    def create(self, strict=False):

        if value := self.exists:
            if strict:
                raise ValueError("Update log already exists!")
            return value

        return self.add(self.initialize_record)

    @property
    def exists(self):
        return bool(len(self))

    def add(self, item: Union[Dict, TransactionLogEntryModel]):
        with self.lock:
            next_seq = len(self)
            if not isinstance(item, TransactionLogEntryModel):
                item["seq"] = next_seq
                item = TransactionLogEntryModel(**item)  # validate item fits model
            elif item.seq != next_seq:
                raise RuntimeError(f"Invalid next seq specified!  Expected {next_seq}, got {item.seq}")

            if item.type is TransactionLogEntryType.init and self.exists:
                raise ValueError("Tried to add another Initialization Record!")

            item_json = item.json()  # generate json
            return self.base_connection.rpush(self.log_name, item_json)

    def get(self, index: int) -> TransactionLogEntryModel:
        item_json = self.base_connection.lindex(self.log_name, index)
        if item_json is None:
            raise IndexError(f"index {index} out of range")
        return TransactionLogEntryModel.parse_raw(item_json)

    def __len__(self):
        return self.base_connection.llen(self.log_name)

    def __getitem__(self, index: Union[slice, int]) -> Union[TransactionLogEntryModel, List[TransactionLogEntryModel]]:
        o_index = index
        if isinstance(index, slice):  # Adapted from https://stackoverflow.com/a/9951672/4875534
            return [self[i] for i in range(*index.indices(len(self)))]

        if isinstance(index, int):
            return self.get(index)

        raise TypeError(f"indices must be integers or slices, not {type(index)}.")


class Rediz:
    cache: ClearableCache  # type hint for IDE's pleasure only

    def __init__(self, config: Config = config):

        # globals
        self.server = config.redis_server
        self.port = config.redis_port
        self.key = config.redis_key
        self.ttl = config.redis_task_ttl
        self.timeout = config.redis_task_timeout
        self.task_result_ttl = config.redis_task_result_ttl
        self.routes = routes.routes
        self.core_q = config.redis_core_q
        # config check if TLS required
        if config.redis_tls_enabled:
            self.base_connection = Redis(
                                        host=self.server,
                                        port=self.port,
                                        password=self.key,
                                        ssl=True,
                                        ssl_cert_reqs='required',
                                        ssl_keyfile=config.redis_tls_key_file,
                                        ssl_certfile=config.redis_tls_cert_file,
                                        ssl_ca_certs=config.redis_tls_ca_cert_file,
                                        socket_connect_timeout=config.redis_socket_connect_timeout,
                                        socket_keepalive=config.redis_socket_keepalive
                                        )
        else:
            self.base_connection = Redis(
                                        host=self.server,
                                        port=self.port,
                                        password=self.key,
                                        socket_connect_timeout=config.redis_socket_connect_timeout,
                                        socket_keepalive=config.redis_socket_keepalive
                                        )
        self.base_q = Queue(self.core_q, connection=self.base_connection)
        self.networked_queuedb = config.redis_queue_store
        self.local_queuedb = {}
        self.local_queuedb[config.redis_fifo_q] = {}
        self.local_queuedb[config.redis_fifo_q]["queue"] = Queue(config.redis_fifo_q, connection=self.base_connection)
        net_db_exists = self.base_connection.get(self.networked_queuedb)
        if not net_db_exists:
            nulldb = json.dumps({"netpalm-db": "queue-val"})
            self.base_connection.set(self.networked_queuedb, nulldb)
        self.cache_enabled = config.redis_cache_enabled
        self.cache_timeout = config.redis_cache_default_timeout
        # we MUST have a prefix, else ".clear()" will drop ALL keys in redis (including those used for the queues).
        self.key_prefix = str(config.redis_cache_key_prefix).strip()
        if not self.key_prefix:
            self.key_prefix = "NOPREFIX"
        if self.cache_enabled:
            log.info(f"Enabling cache!")
            self.cache = ClearableCache(self.base_connection, default_timeout=self.cache_timeout,
                                        key_prefix=self.key_prefix)
        else:
            log.info(f"Disabling cache!")
            # noinspection PyTypeChecker
            self.cache = DisabledCache()
        self.extn_update_log = ExtnUpdateLog(self.base_connection, config.redis_update_log)

    def check_worker_is_alive(self, q):
        """
        checks if a worker exists on a given queue
        """
        try:
            queue = Queue(q)
            workers = Worker.all(connection=self.base_connection, queue=queue)
            if len(workers) >= 1:
                return True
        except Exception as e:
            log.error(f"check_worker_is_alive: {e}")
            return False

    def getqueue(self, host):
        """
        checks whether a queue exists and worker exists
        accross the controller, redis and worker node
        """
        # checks a centralised db / queue exists and creates a empty db if one does not exist
        try:
            # check the redis db store for a queue
            result = self.base_connection.get(self.networked_queuedb)
            if result:
                jsresult = json.loads(result)
                res = jsresult.get(host, False)
                if res:
                    # check the worker is running
                    if self.check_worker_is_alive(host):
                        q_exists_in_local_db = self.local_queuedb.get(host, False)
                        # check if the local controller queue db is out of sync with the networked db
                        if not q_exists_in_local_db:
                            self.local_queuedb[host] = {}
                            self.local_queuedb[host]["queue"] = Queue(host, connection=self.base_connection)
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        except Exception as e:
            return e

    def get_redis_meta_template(self):
        meta_template = {
            "errors": [],
            "enqueued_elapsed_seconds": None,
            "started_elapsed_seconds": None,
            "total_elapsed_seconds": None,
            "result": ""
        }
        return meta_template

    def create_queue_worker(self, qname):
        from netpalm.netpalm_pinned_worker import pinned_worker_constructor
        try:
            log.info(f"create_queue_worker: creating queue and worker {qname}")
            meta_template = self.get_redis_meta_template()
            result = self.base_connection.get(self.networked_queuedb)
            tmpdb = json.loads(result)
            tmpdb[qname] = True
            jsresult = json.dumps(tmpdb)
            self.base_connection.set(self.networked_queuedb, jsresult)
            self.base_q.enqueue_call(func=pinned_worker_constructor, args=(qname,), meta=meta_template,
                                     ttl=self.ttl, result_ttl=self.task_result_ttl)
            self.local_queuedb[qname] = {}
            self.local_queuedb[qname]["queue"] = Queue(qname, connection=self.base_connection)
            return self.local_queuedb[qname]["queue"]
        except Exception as e:
            return e

    def check_and_create_q_w(self, hst):
        qexists = self.getqueue(hst)
        if not qexists:
            self.create_queue_worker(hst)

    def render_task_response(self, task_job):
        created_at = str(task_job.created_at)
        enqueued_at = str(task_job.enqueued_at)
        started_at = str(task_job.started_at)
        ended_at = str(task_job.ended_at)

        try:

            current_time = datetime.datetime.utcnow()
            created_parsed_time = datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f")

            # if enqueued but not started calculate time
            if enqueued_at != "None" and enqueued_at and started_at == "None":
                parsed_time = datetime.datetime.strptime(enqueued_at, "%Y-%m-%d %H:%M:%S.%f")
                task_job.meta["enqueued_elapsed_seconds"] = (current_time - parsed_time).seconds
                task_job.save()

            # if created but not finished calculate time
            if ended_at != "None" and ended_at:
                parsed_time = datetime.datetime.strptime(ended_at, "%Y-%m-%d %H:%M:%S.%f")
                task_job.meta["total_elapsed_seconds"] = (parsed_time - created_parsed_time).seconds
                task_job.save()

            elif ended_at == "None":
                task_job.meta["total_elapsed_seconds"] = (current_time - created_parsed_time).seconds
                task_job.save()

            #clean up vars for response
            created_at = None if created_at == "None" else created_at
            enqueued_at = None if enqueued_at == "None" else enqueued_at
            started_at = None if started_at == "None" else started_at
            ended_at = None if ended_at == "None" else ended_at

        except Exception as e:
            log.error(f"render_task_response : {str(e)}")
            pass

        resultdata = None
        resultdata = Response(status="success", data={
            "task_id": task_job.get_id(),
            "created_on": created_at,
            "task_queue": task_job.description,
            "task_meta": {
                "enqueued_at": enqueued_at,
                "started_at": started_at,
                "ended_at": ended_at,
                "enqueued_elapsed_seconds": task_job.meta["enqueued_elapsed_seconds"],
                "total_elapsed_seconds": task_job.meta["total_elapsed_seconds"]
            },
            "task_status": task_job.get_status(),
            "task_result": task_job.result,
            "task_errors": task_job.meta["errors"]
        }).dict()
        return resultdata

    def sendtask(self, q, exe, **kwargs):
        meta_template = self.get_redis_meta_template()
        task = self.local_queuedb[q]["queue"].enqueue_call(func=self.routes[exe], description=q, ttl=self.ttl,
                                                           result_ttl=self.task_result_ttl, kwargs=kwargs["kwargs"],
                                                           meta=meta_template, timeout=self.timeout)
        resultdata = self.render_task_response(task)
        return resultdata

    def execute_task(self, method, **kwargs):
        kw = kwargs.get("kwargs", False)
        connectionargs = kw.get("connection_args", False)
        host = False
        if connectionargs:
            host = kw["connection_args"].get("host", False)
        queue_strategy = kw.get("queue_strategy", False)
        if queue_strategy == "pinned":
            self.check_and_create_q_w(hst=host)
            r = self.sendtask(q=host, exe=method, kwargs=kw)
        else:
            r = self.sendtask(q=config.redis_fifo_q, exe=method, kwargs=kw)
        return r

    def execute_service_task(self, metho, **kwargs):
        """service wrapper for execute task method"""
        log.info(kwargs)
        kw = kwargs.get("kwargs")
        resul = self.execute_task(method=metho, kwargs=kw)
        serv = self.create_service_instance(raw_data=kw)
        if serv:
            resul["data"]["service_id"] = serv
        return resul

    def fetchsubtask(self, parent_task_object):
        """fetches nested subtasks for service driven tasks"""
        try:
            status = parent_task_object["data"]["task_status"]
            log.info(f'fetching subtask: {parent_task_object["data"]["task_id"]}')
            task_errors = []
            for j in range(len(parent_task_object["data"]["task_result"])):
                tempres = Job.fetch(parent_task_object["data"]["task_result"][j]["data"]["data"]["task_id"], connection=self.base_connection)
                temprespobj = self.render_task_response(tempres)
                if status != "started" or status != "queued":
                    if temprespobj["data"]["task_status"] == "started":
                        parent_task_object["data"]["task_status"] = temprespobj["data"]["task_status"]
                if len(temprespobj["data"]["task_errors"]) >= 1:
                    task_errors.append({
                        parent_task_object["data"]["task_result"][j]["host"]:{
                            "task_id":parent_task_object["data"]["task_result"][j]["data"]["data"]["task_id"],
                            "task_errors":temprespobj["data"]["task_errors"]
                        }
                        })
                parent_task_object["data"]["task_result"][j]["data"].update(temprespobj)
            if len(task_errors) >= 1:
                parent_task_object["data"]["task_errors"] = task_errors
            return parent_task_object

        except Exception as e:
            return e

    def fetchtask(self, task_id):
        log.info(f"fetching task: {task_id}")
        try:
            task = Job.fetch(task_id, connection=self.base_connection)
            response_object = self.render_task_response(task)
            if "task_id" in str(response_object["data"]["task_result"]) and "operation" in str(response_object["data"]["task_result"]):
                response_object = self.fetchsubtask(parent_task_object=response_object)
            return response_object
        except Exception as e:
            return e

    def getjoblist(self, q):
        try:
            self.getqueue(q)
            # if single host lookup
            if q:
                qexists = self.local_queuedb.get(q, False)
                if qexists:
                    t = self.local_queuedb[q]["queue"].get_job_ids()
                    if t:
                        response_object = {
                            "status": "success",
                            "data": {
                                "task_id": t
                            }
                        }
                        return response_object
                    else:
                        return False
                else:
                    return False
            #multi host lookup
            elif not q:
                response_object = {
                    "status": "success",
                    "data": {
                        "task_id": []
                    }
                }
                for i in self.local_queuedb:
                    response_object["data"]["task_id"].append(self.local_queuedb[i]["queue"].get_job_ids())
                return response_object
        except Exception as e:
            return e

    def getjobliststatus(self, q):
        log.info(f"getting jobs and status: {q}")
        try:
            if q:
                self.getqueue(q)
                task = self.local_queuedb[q]["queue"].get_job_ids()
                response_object = {
                    "status": "success",
                    "data": {
                        "task_id": []
                    }
                }
                # get startedjobs
                startedjobs = self.getstartedjobs(self.local_queuedb[q]["queue"])
                for job in startedjobs:
                    task.append(job)

                # get finishedjobs
                finishedjobs = self.getfinishedjobs(self.local_queuedb[q]["queue"])
                for job in finishedjobs:
                    task.append(job)

                # get failedjobs
                failedjobs = self.getfailedjobs(self.local_queuedb[q]["queue"])
                for job in failedjobs:
                    task.append(job)

                if task:
                    for job in task:
                        try:
                            jobstatus = Job.fetch(job, connection=self.base_connection)
                            jobdata = self.render_task_response(jobstatus)
                            response_object["data"]["task_id"].append(jobdata)
                        except Exception as e:
                            return e
                            pass
                return response_object
        except Exception as e:
            return e

    def getstartedjobs(self, q):
        log.info(f"getting started jobs: {q}")
        try:
            registry = StartedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def getfinishedjobs(self, q):
        log.info(f"getting finished jobs: {q}")
        try:
            registry = FinishedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def getfailedjobs(self, q):
        log.info(f"getting failed jobs: {q}")
        try:
            registry = FailedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def send_broadcast(self, msg: str):
        log.info(f"sending broadcast: {msg}")
        try:
            self.base_connection.publish(config.redis_broadcast_q, msg)
            return {
                "result": "Message Sent"
            }

        except Exception as e:
            return e

    def clear_cache_for_host(self, cache_key: str):
        if not cache_key.count(":") >= 2:
            log.error(f"{cache_key=} doesn't seem to be a valid cache key!")
        host_port = cache_key.split(":")[:2]  # first 2 segments
        modified_cache_key = ":".join(host_port)
        log.info(f"deleting {modified_cache_key=}")
        return self.cache.clear_keys(modified_cache_key)

    def get_workers(self):
        """returns stats about all running rq workers"""
        try:
            workers = Worker.all(connection=self.base_connection)
            result = []
            for w in workers:
                w_bd = str(w.birth_date)
                w_lhb = str(w.last_heartbeat)
                birth_d = datetime.datetime.strptime(w_bd, "%Y-%m-%d %H:%M:%S.%f")
                last_hb = datetime.datetime.strptime(w_lhb, "%Y-%m-%d %H:%M:%S.%f")
                result.append(WorkerResponse(
                    hostname=w.hostname,
                    pid=w.pid,
                    name=w.name,
                    last_heartbeat=last_hb,
                    birth_date=birth_d,
                    successful_job_count=w.successful_job_count,
                    failed_job_count=w.failed_job_count,
                    total_working_time=w.total_working_time
                ).dict())
            return result
        except Exception as e:
            log.error(f"get_workers: {e}")
            return e

    def kill_worker(self, worker_name=False):
        """kills a worker by its name"""
        running_workers = self.get_workers()
        killed = False
        for w in running_workers:
            if w["name"] == worker_name:
                killed = True
                kill_message = {
                    "type": "kill_worker_pid",
                    "kwargs": {
                        "hostname": w["hostname"],
                        "pid": w["pid"]
                        }
                    }
                self.send_broadcast(json.dumps(kill_message))
        if not killed:
            raise Exception(f"worker {worker_name} not found")

    def create_service_instance(self, raw_data):
        """creates a service id and stores it in the DB with the service
        payload"""
        u_uid = uuid.uuid4()
        sid = f"{1}_{u_uid}_service_instance"
        exists = self.base_connection.get(sid)
        if not exists:
            raw_json = json.dumps(raw_data)
            self.base_connection.set(sid, raw_json)
            self.base_connection.bgsave()
            return f"{u_uid}"
        else:
            return False

    def fetch_service_instance(self, sid):
        """returns ALL data from the latest copy of the latest service"""
        sid_parsed = f"1_{sid}_service_instance"
        exists = self.base_connection.get(sid_parsed)
        if not exists:
            return False
        else:
            return exists

    def fetch_service_instance_args(self, sid):
        """returns the args ONLY from the latest copy of the latest service"""
        service_inst_result = self.fetch_service_instance(sid)
        if service_inst_result:
            # scrub credentials
            service_inst_json = json.loads(service_inst_result)["args"]
            json_scrub_dict = ["$.username", "$.password", "$.key"]
            for scrub_match in json_scrub_dict:
                jsonpath_expr = parse(scrub_match)
                jsonpath_expr.find(service_inst_json)
                jsonpath_expr.update(service_inst_json, "*******")
            return service_inst_json
        else:
            return False

    def delete_service_instance(self, sid):
        """gets the service instance and deletes it from the db and network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "delete"
        result = self.execute_task(method="render_service", kwargs=res)
        self.base_connection.delete(sid_parsed)
        self.base_connection.bgsave()
        return result

    def redeploy_service_instance(self, sid):
        """redeploys the service instance to the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "create"
        result = self.execute_task(method="render_service", kwargs=res)
        return result

    def retrieve_service_instance(self, sid):
        """validates the service instances state against the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "retrieve"
        result = self.execute_task(method="render_service", kwargs=res)
        return result

    def validate_service_instance(self, sid):
        """validates the service instances state against the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "validate"
        result = self.execute_task(method="render_service", kwargs=res)
        return result

    def get_service_instances(self):
        """retrieves all service instances in the redis store"""
        result = []
        for sid in self.base_connection.scan_iter("*_service_instance"):
            sid_str = sid.decode("utf-8")
            parsed_sid = sid_str.replace('1_', '').replace('_service_instance', '')
            log.info(parsed_sid)
            sid_data = json.loads(self.fetch_service_instance(parsed_sid))
            if sid_data:
                appendres = {
                    "service_model": sid_data["service_model"],
                    "service_id": parsed_sid
                    }
                result.append(appendres)
        return result

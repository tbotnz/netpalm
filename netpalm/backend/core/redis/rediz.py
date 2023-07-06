import datetime
import json
import logging
from logging import error
from typing import Union, Dict, List

from jsonpath_ng import jsonpath, parse

import redis_lock
from cachelib import RedisCache

import uuid

from redis import Redis
from redis.exceptions import ConnectionError
from rq import Queue, Worker
from rq.job import Job
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

from netpalm.backend.core.confload.confload import config, Config
from netpalm.backend.core.models.task import Response, WorkerResponse
from netpalm.backend.core.models.service import (
    ServiceInstanceData,
    ServiceInstanceState,
)
from netpalm.backend.core.models.transaction_log import (
    TransactionLogEntryModel,
    TransactionLogEntryType,
)
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
        self.lock = redis_lock.Lock(
            base_connection, config.redis_update_log, expire=30, auto_renewal=True
        )  # lock should only expire if a process dies
        self.initialize_record = {
            "type": TransactionLogEntryType.init,
            "data": {"init": True},
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
                raise RuntimeError(
                    f"Invalid next seq specified!  Expected {next_seq}, got {item.seq}"
                )

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

    def __getitem__(
        self, index: Union[slice, int]
    ) -> Union[TransactionLogEntryModel, List[TransactionLogEntryModel]]:
        o_index = index
        if isinstance(
            index, slice
        ):  # Adapted from https://stackoverflow.com/a/9951672/4875534
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
                ssl_cert_reqs="required",
                ssl_keyfile=config.redis_tls_key_file,
                ssl_certfile=config.redis_tls_cert_file,
                ssl_ca_certs=config.redis_tls_ca_cert_file,
                socket_connect_timeout=config.redis_socket_connect_timeout,
                socket_keepalive=config.redis_socket_keepalive,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError],
            )
        else:
            self.base_connection = Redis(
                host=self.server,
                port=self.port,
                password=self.key,
                socket_connect_timeout=config.redis_socket_connect_timeout,
                socket_keepalive=config.redis_socket_keepalive,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError],
            )
        #        self.base_q = Queue(self.core_q, connection=self.base_connection)
        self.networked_queuedb = config.redis_queue_store
        self.redis_pinned_store = config.redis_pinned_store

        self.local_queuedb = {}
        self.local_queuedb[config.redis_fifo_q] = {}
        self.local_queuedb[config.redis_fifo_q]["queue"] = Queue(
            config.redis_fifo_q, connection=self.base_connection
        )

        # init networked db for processes queues
        net_db_exists = self.base_connection.get(self.networked_queuedb)
        if not net_db_exists:
            null_network_db = json.dumps({"netpalm-db": "queue-val"})
            self.base_connection.set(self.networked_queuedb, null_network_db)

        # init pinned db
        pinned_db_exists = self.base_connection.get(self.redis_pinned_store)
        if not pinned_db_exists:
            null_pinned_db = json.dumps([])
            self.base_connection.set(self.redis_pinned_store, null_pinned_db)

        self.cache_enabled = config.redis_cache_enabled
        self.cache_timeout = config.redis_cache_default_timeout
        # we MUST have a prefix, else ".clear()" will drop ALL keys in redis (including those used for the queues).
        self.key_prefix = str(config.redis_cache_key_prefix).strip()
        if not self.key_prefix:
            self.key_prefix = "NOPREFIX"
        if self.cache_enabled:
            log.info(f"Enabling cache!")
            self.cache = ClearableCache(
                self.base_connection,
                default_timeout=self.cache_timeout,
                key_prefix=self.key_prefix,
            )
        else:
            log.info(f"Disabling cache!")
            # noinspection PyTypeChecker
            self.cache = DisabledCache()
        self.extn_update_log = ExtnUpdateLog(
            self.base_connection, config.redis_update_log
        )

    def __append_network_queue_db(self, qn):
        """appends to the networked queue db"""
        result = self.base_connection.get(self.networked_queuedb)
        tmpdb = json.loads(result)
        tmpdb[qn] = True
        jsresult = json.dumps(tmpdb)
        self.base_connection.set(self.networked_queuedb, jsresult)

    def __append_local_queue_db(self, qn):
        """appends to the local queue db"""
        self.local_queuedb[qn] = {}
        self.local_queuedb[qn]["queue"] = Queue(qn, connection=self.base_connection)
        return self.local_queuedb[qn]["queue"]

    def __exists_in_local_queue_db(self, qn):
        q_exists_in_local_db = self.local_queuedb.get(qn, False)
        return q_exists_in_local_db

    def __worker_is_alive(self, q):
        """checks if a worker exists on a given queue"""
        try:
            queue = Queue(q, connection=self.base_connection)
            workers = Worker.all(queue=queue)
            if len(workers) >= 1:
                return True
            else:
                log.info(f"worker required for {q}")
                return False
        except Exception as e:
            log.error(f"__worker_is_alive: {e}")
            return False

    def __getqueue(self, host):
        """
        checks whether a queue exists and worker exists
        accross the controller, redis and worker node.
        creates a local queue if required
        """
        # checks a centralised db / queue exists and creates a empty db if one does not exist
        try:
            # check the redis db store for a queue
            result = self.base_connection.get(self.networked_queuedb)
            jsresult = json.loads(result)
            res = jsresult.get(host, False)
            # if exists on the networked db, check whether you have a local connection
            if res:
                if not self.__worker_is_alive(host):
                    return False
                # create a local connection if required
                if not self.__exists_in_local_queue_db(qn=host):
                    self.__append_local_queue_db(qn=host)
                return True
            else:
                return False

        except Exception as e:
            return e

    def __get_redis_meta_template(self):
        """template for redis meta data"""
        meta_template = {
            "errors": [],
            "enqueued_elapsed_seconds": None,
            "started_elapsed_seconds": None,
            "total_elapsed_seconds": None,
            "result": "",
        }
        return meta_template

    def __create_queue_worker(self, pinned_container_queue, pinned_worker_qname):
        """
        creates a local queue on the worker and executes a rpc to create a
        pinned worker on a remote container
        """
        from netpalm.netpalm_pinned_worker import pinned_worker_constructor

        try:
            log.info(
                f"__create_queue_worker: creating queue and worker {pinned_worker_qname}"
            )
            meta_template = self.__get_redis_meta_template()
            self.__append_network_queue_db(qn=pinned_worker_qname)
            self.local_queuedb[pinned_container_queue]["queue"].enqueue_call(
                func=pinned_worker_constructor,
                args=(pinned_worker_qname,),
                meta=meta_template,
                ttl=self.ttl,
                result_ttl=self.task_result_ttl,
            )
            r = self.__append_local_queue_db(qn=pinned_worker_qname)
            return r
        except Exception as e:
            return e

    def reoute_and_create_q_worker(self, hst):
        """routes a process to the correct container."""
        qexists = self.__getqueue(hst)
        if not qexists:
            # check for process availability:
            pinned_hosts = self.fetch_pinned_store()
            capacity = False
            # find first available container with process capacity
            for host in pinned_hosts:
                if host["count"] < host["limit"]:
                    # create in the local db if required
                    if not self.__exists_in_local_queue_db(
                        qn=host["pinned_listen_queue"]
                    ):
                        self.__append_local_queue_db(qn=host["pinned_listen_queue"])
                    self.__create_queue_worker(
                        pinned_container_queue=host["pinned_listen_queue"],
                        pinned_worker_qname=hst,
                    )
                    capacity = True
                    break
            # throw exception if no capcity found
            if not capacity:
                err = """Not enough pinned worker process capacity: kill pinned
                 processes or spin up more pinned workers!"""
                log.error(err)
                raise Exception(f"{err}")

    def __render_task_response(self, task_job):
        """formats and returns the task rpc jobs result"""
        created_at = str(task_job.created_at)
        enqueued_at = str(task_job.enqueued_at)
        started_at = str(task_job.started_at)
        ended_at = str(task_job.ended_at)

        try:

            current_time = datetime.datetime.utcnow()
            created_parsed_time = datetime.datetime.strptime(
                created_at, "%Y-%m-%d %H:%M:%S.%f"
            )

            # if enqueued but not started calculate time
            if enqueued_at != "None" and enqueued_at and started_at == "None":
                parsed_time = datetime.datetime.strptime(
                    enqueued_at, "%Y-%m-%d %H:%M:%S.%f"
                )
                task_job.meta["enqueued_elapsed_seconds"] = (
                    current_time - parsed_time
                ).seconds

            # if created but not finished calculate time
            if ended_at != "None" and ended_at:
                parsed_time = datetime.datetime.strptime(
                    ended_at, "%Y-%m-%d %H:%M:%S.%f"
                )
                task_job.meta["total_elapsed_seconds"] = (
                    parsed_time - created_parsed_time
                ).seconds

            elif ended_at == "None":
                task_job.meta["total_elapsed_seconds"] = (
                    current_time - created_parsed_time
                ).seconds

            task_job.save()

            # clean up vars for response
            created_at = None if created_at == "None" else created_at
            enqueued_at = None if enqueued_at == "None" else enqueued_at
            started_at = None if started_at == "None" else started_at
            ended_at = None if ended_at == "None" else ended_at

        except Exception as e:
            log.error(f"__render_task_response : {str(e)}")
            pass

        resultdata = Response(
            status="success",
            data={
                "task_id": task_job.get_id(),
                "created_on": created_at,
                "task_queue": task_job.description,
                "task_meta": {
                    "enqueued_at": enqueued_at,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "enqueued_elapsed_seconds": task_job.meta[
                        "enqueued_elapsed_seconds"
                    ],
                    "total_elapsed_seconds": task_job.meta["total_elapsed_seconds"],
                    "assigned_worker": task_job.meta.get("assigned_worker"),
                },
                "task_status": task_job.get_status(),
                "task_result": task_job.result,
                "task_errors": task_job.meta["errors"],
            },
        ).dict()
        return resultdata

    def sendtask(self, q, exe, **kwargs):
        log.debug(f'sendtask: {kwargs["kwargs"]}')
        ttl = kwargs["kwargs"].get("ttl")
        meta_template = self.__get_redis_meta_template()
        if not ttl:
            task = self.local_queuedb[q]["queue"].enqueue_call(
                func=self.routes[exe],
                description=q,
                ttl=self.ttl,
                result_ttl=self.task_result_ttl,
                kwargs=kwargs["kwargs"],
                meta=meta_template,
                timeout=self.timeout,
            )
        else:
            task = self.local_queuedb[q]["queue"].enqueue_call(
                func=self.routes[exe],
                description=q,
                ttl=ttl,
                result_ttl=ttl,
                kwargs=kwargs["kwargs"],
                meta=meta_template,
                timeout=ttl,
            )
        resultdata = self.__render_task_response(task)
        return resultdata

    def execute_task(self, method, **kwargs):
        """main entry point for rpc tasks"""
        kw = kwargs.get("kwargs", False)
        connectionargs = kw.get("connection_args", False)
        host = False
        if connectionargs:
            host = kw["connection_args"].get("host", False)
        queue_strategy = kw.get("queue_strategy", False)
        if queue_strategy == "pinned":
            self.reoute_and_create_q_worker(hst=host)
            r = self.sendtask(q=host, exe=method, kwargs=kw)
        else:
            r = self.sendtask(q=config.redis_fifo_q, exe=method, kwargs=kw)
        return r

    def execute_create_service_task(self, metho, model, **kwargs):
        """service wrapper for execute task method"""

        kw = kwargs.get("kwargs")
        current_time = datetime.datetime.utcnow()
        created_parsed_time = datetime.datetime.strftime(
            current_time, "%Y-%m-%d %H:%M:%S.%f"
        )
        u_uid_v = uuid.uuid4()

        service_data = ServiceInstanceData(
            service_meta={
                "service_model": model,
                "created_at": created_parsed_time,
                "updated_at": None,
                "service_id": f"{u_uid_v}",
            },
            service_data=kw,
        ).dict()

        resul = self.execute_task(method=metho, kwargs=service_data)
        serv = self.__create_service_instance(raw_data=service_data, u_uid=u_uid_v)
        if serv:
            resul["data"]["service_id"] = serv
        return resul

    def __fetchsubtask(self, parent_task_object):
        """fetches nested subtasks for service driven tasks"""
        try:
            status = parent_task_object["data"]["task_status"]
            log.info(f'fetching subtask: {parent_task_object["data"]["task_id"]}')
            task_errors = []
            for j in range(len(parent_task_object["data"]["task_result"])):
                tempres = Job.fetch(
                    parent_task_object["data"]["task_result"][j]["data"]["data"][
                        "task_id"
                    ],
                    connection=self.base_connection,
                )
                temprespobj = self.__render_task_response(tempres)
                if status != "started" or status != "queued":
                    if temprespobj["data"]["task_status"] == "started":
                        parent_task_object["data"]["task_status"] = temprespobj["data"][
                            "task_status"
                        ]
                if temprespobj["data"]["task_status"] == "failed":
                    task_errors.append(
                        {
                            parent_task_object["data"]["task_result"][j]["host"]: {
                                "task_id": parent_task_object["data"]["task_result"][j][
                                    "data"
                                ]["data"]["task_id"],
                                "task_errors": temprespobj["data"]["task_errors"],
                            }
                        }
                    )
                parent_task_object["data"]["task_result"][j]["data"].update(temprespobj)
            if len(task_errors) >= 1:
                parent_task_object["data"]["task_errors"] = task_errors
            return parent_task_object

        except Exception as e:
            return e

    def fetchtask(self, task_id):
        """gets a job result and renders it"""
        log.info(f"fetching task: {task_id}")
        try:
            task = Job.fetch(task_id, connection=self.base_connection)
            response_object = self.__render_task_response(task)
            if "task_id" in str(
                response_object["data"]["task_result"]
            ) and "operation" in str(response_object["data"]["task_result"]):
                response_object = self.__fetchsubtask(
                    parent_task_object=response_object
                )
            return response_object
        except Exception as e:
            return e

    def getjoblist(self, q):
        """provides a list of all jobs in the queue"""
        try:
            self.__getqueue(q)
            # if single host lookup
            if q:
                if self.__exists_in_local_queue_db(qn=q):
                    t = self.local_queuedb[q]["queue"].get_job_ids()
                    if t:
                        response_object = {"status": "success", "data": {"task_id": t}}
                        return response_object
                    else:
                        return False
                else:
                    return False
            # multi host lookup
            elif not q:
                response_object = {"status": "success", "data": {"task_id": []}}
                for i in self.local_queuedb:
                    res = self.local_queuedb[i]["queue"].get_job_ids()
                    if res:
                        response_object["data"]["task_id"].append(res)
                return response_object
        except Exception as e:
            return e

    def getjobliststatus(self, q):
        """provides a breakdown of all jobs in the queue"""
        log.info(f"getting jobs and status: {q}")
        try:
            if q:
                self.__getqueue(q)
                task = self.local_queuedb[q]["queue"].get_job_ids()
                response_object = {"status": "success", "data": {"task_id": []}}
                # get startedjobs
                startedjobs = self.__getstartedjobs(self.local_queuedb[q]["queue"])
                for job in startedjobs:
                    task.append(job)

                # get finishedjobs
                finishedjobs = self.__getfinishedjobs(self.local_queuedb[q]["queue"])
                for job in finishedjobs:
                    task.append(job)

                # get failedjobs
                failedjobs = self.__getfailedjobs(self.local_queuedb[q]["queue"])
                for job in failedjobs:
                    task.append(job)

                if task:
                    for job in task:
                        try:
                            jobstatus = Job.fetch(job, connection=self.base_connection)
                            jobdata = self.__render_task_response(jobstatus)
                            response_object["data"]["task_id"].append(jobdata)
                        except Exception as e:
                            return e
                            pass
                return response_object
        except Exception as e:
            return e

    def __getstartedjobs(self, q):
        """returns list of started redis jobs"""
        log.info(f"getting started jobs: {q}")
        try:
            registry = StartedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def __getfinishedjobs(self, q):
        """returns list of finished redis jobs"""
        log.info(f"getting finished jobs: {q}")
        try:
            registry = FinishedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def __getfailedjobs(self, q):
        """returns list of failed redis jobs"""
        log.info(f"getting failed jobs: {q}")
        try:
            registry = FailedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def send_broadcast(self, msg: str):
        """publishes a message to all workers"""
        log.info(f"sending broadcast: {msg}")
        try:
            self.base_connection.publish(config.redis_broadcast_q, msg)
            return {"result": "Message Sent"}

        except Exception as e:
            return e

    def clear_cache_for_host(self, cache_key: str):
        """poisions a cache for a specific host"""
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
                result.append(
                    WorkerResponse(
                        hostname=w.hostname,
                        pid=w.pid,
                        name=w.name,
                        last_heartbeat=last_hb,
                        birth_date=birth_d,
                        successful_job_count=w.successful_job_count,
                        failed_job_count=w.failed_job_count,
                        total_working_time=w.total_working_time,
                    ).dict()
                )
            return result
        except Exception as e:
            log.error(f"get_workers: {e}")
            return e

    def kill_worker(self, worker_name=False):
        """kills a worker by its name and updates the pinned worker db"""
        running_workers = self.get_workers()
        killed = False
        for w in running_workers:
            if w["name"] == worker_name:
                killed = True
                kill_message = {
                    "type": "kill_worker_pid",
                    "kwargs": {"hostname": w["hostname"], "pid": w["pid"]},
                }
                self.send_broadcast(json.dumps(kill_message))

                # update pinned db
                r = self.base_connection.get(self.redis_pinned_store)
                rjson = json.loads(r)
                for container in rjson:
                    if container["hostname"] == w["hostname"]:
                        container["count"] -= 1
                self.base_connection.set(self.redis_pinned_store, json.dumps(rjson))

        if not killed:
            raise Exception(f"worker {worker_name} not found")

    def __create_service_instance(self, raw_data, u_uid):
        """creates a service id and stores it in the DB with the service
        payload"""
        sid = f"{1}_{u_uid}_service_instance"
        exists = self.base_connection.get(sid)
        if not exists:
            raw_json = json.dumps(raw_data)
            log.debug(
                f"__create_service_instance: creating service instance {sid} with attrs {raw_json}"
            )
            self.base_connection.set(sid, raw_json)
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

    def update_service_instance_data(self, sid, new_data):
        data = self.fetch_service_instance(sid)
        if data:
            sid_parsed = f"1_{sid}_service_instance"
            # add a backup transaction thing prior to delete in future
            self.base_connection.delete(sid_parsed)
            current_time = datetime.datetime.utcnow()
            created_parsed_time = datetime.datetime.strftime(
                current_time, "%Y-%m-%d %H:%M:%S.%f"
            )
            new_data["service_meta"]["updated_at"] = created_parsed_time
            self.__create_service_instance(raw_data=new_data, u_uid=sid)

    def set_service_instance_status(self, sid, state: ServiceInstanceState):
        log.debug(f"set_service_instance_status: {sid} {state}")
        data = self.fetch_service_instance(sid)
        if data:
            service_json = json.loads(data)
            service_json["service_meta"]["service_state"] = state
            self.update_service_instance_data(sid, service_json)

    def fetch_service_instance_args(self, sid):
        log.debug(f"fetch_service_instance_args: {sid}")
        """returns the args ONLY from the latest copy of the latest service"""
        service_inst_result = self.fetch_service_instance(sid)
        if service_inst_result:
            log.debug(f"fetch_service_instance_args: {service_inst_result}")
            # scrub credentials
            service_inst_json = json.loads(service_inst_result)
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
        result = self.execute_task(method="service_delete", kwargs=res)
        self.base_connection.delete(sid_parsed)
        return result

    def redeploy_service_instance(self, sid):
        """redeploys the service instance to the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "create"
        result = self.execute_task(method="service_re_deploy", kwargs=res)
        return result

    def retrieve_service_instance(self, sid):
        """validates the service instances state against the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "retrieve"
        result = self.execute_task(method="service_retrieve", kwargs=res)
        return result

    def validate_service_instance(self, sid):
        """validates the service instances state against the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "validate"
        result = self.execute_task(method="service_validate", kwargs=res)
        return result

    def health_check_service_instance(self, sid):
        """health check the service instances state against the network"""
        sid_parsed = f"1_{sid}_service_instance"
        res = json.loads(self.fetch_service_instance(sid))
        res["operation"] = "validate"
        result = self.execute_task(method="service_health_check", kwargs=res)
        return result

    def get_service_instances(self):
        """retrieves all service instances in the redis store"""
        result = []
        for sid in self.base_connection.scan_iter("*_service_instance"):
            sid_str = sid.decode("utf-8")
            parsed_sid = sid_str.replace("1_", "").replace("_service_instance", "")
            sid_data = json.loads(self.fetch_service_instance(parsed_sid))
            if sid_data:
                result.append(sid_data["service_meta"])
        return result

    def fetch_pinned_store(self):
        """returns ALL data from the pinned store"""
        exists = self.base_connection.get(config.redis_pinned_store)
        result = json.loads(exists)
        return result

    def purge_container_from_pinned_store(self, name):
        """force purge a specific container from the pinned store"""
        r = self.base_connection.get(config.redis_pinned_store)
        rjson = json.loads(r)
        idex = 0
        for container in rjson:
            if container["hostname"] == name:
                rjson.pop(idex)
                self.base_connection.set(config.redis_pinned_store, json.dumps(rjson))
                break
            idex += 1

    def deregister_worker(self, container):
        """finds and deregisters an rq worker"""
        # purge all workers still running on this container
        workers = Worker.all(connection=self.base_connection)
        for worker in workers:
            if worker.hostname == f"{container}":
                worker.register_death()

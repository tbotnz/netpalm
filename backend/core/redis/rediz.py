import datetime
import json
import logging

from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
from starlette.routing import NoMatchFound

from backend.core.confload.confload import config
from backend.core.models.task import model_response
from backend.core.routes import routes
from netpalm_pinned_worker import pinned_worker_constructor

log = logging.getLogger(__name__)


class rediz:

    def __init__(self):

        # globals
        self.server = config.redis_server
        self.port = config.redis_port
        self.key = config.redis_key
        self.ttl = config.redis_task_ttl
        self.timeout = config.redis_task_timeout
        self.task_result_ttl = config.redis_task_result_ttl
        self.routes = routes.routes
        self.core_q = config.redis_core_q
        self.base_connection = Redis(host=self.server, port=self.port, password=self.key)
        self.base_q = Queue(self.core_q, connection=self.base_connection)
        self.networked_queuedb = config.redis_queue_store
        self.local_queuedb = {}
        self.local_queuedb[config.redis_fifo_q] = {}
        self.local_queuedb[config.redis_fifo_q]["queue"] = Queue(config.redis_fifo_q, connection=self.base_connection)
        net_db_exists = self.base_connection.get(self.networked_queuedb)
        if not net_db_exists:
            nulldb = json.dumps({"netpalm-db":"queue-val"})
            self.base_connection.set(self.networked_queuedb, nulldb)

    def getqueue(self, host):
        #checks a centralised db / queue exists and creates a empty db if one does not exist
        try:
            #check the db store for something
            result = self.base_connection.get(self.networked_queuedb)
            if result:
                jsresult = json.loads(result)
                res = jsresult.get(host, False)
                #check if the local controller queue db is out of sync with the networked db
                if res:
                    q_exists_in_local_db = self.local_queuedb.get(host, False)
                    if not q_exists_in_local_db:
                        self.local_queuedb[host] = {}
                        self.local_queuedb[host]["queue"] = Queue(host, connection=self.base_connection)
                    return True
                elif not res:
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
        try:
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
        try:
            qexists = self.getqueue(hst)
            if not qexists:
                self.create_queue_worker(hst)
        except Exception as e:
            return e

    def render_task_response(self, task_job):
        created_at = str(task_job.created_at)
        enqueued_at = str(task_job.enqueued_at)
        started_at = str(task_job.started_at)
        ended_at = str(task_job.ended_at)

        try:

            current_time = datetime.datetime.utcnow()
            created_parsed_time = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')

            #if enqueued but not started calculate time
            if enqueued_at != "None" and enqueued_at and started_at == "None":
                parsed_time = datetime.datetime.strptime(enqueued_at, '%Y-%m-%d %H:%M:%S.%f')
                task_job.meta["enqueued_elapsed_seconds"] = (current_time - parsed_time).seconds
                task_job.save()

            #if created but not finished calculate time
            if ended_at != "None" and ended_at:
                parsed_time = datetime.datetime.strptime(ended_at, '%Y-%m-%d %H:%M:%S.%f')
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
            log.error(f'render_task_response : {str(e)}')
            pass

        resultdata = None
        resultdata = model_response(status="success",data={
            "task_id":task_job.get_id(),
            "created_on":created_at,
            "task_queue":task_job.description,
            "task_meta":{
                "enqueued_at":enqueued_at,
                "started_at":started_at,
                "ended_at": ended_at,
                "enqueued_elapsed_seconds": task_job.meta["enqueued_elapsed_seconds"],
                "total_elapsed_seconds": task_job.meta["total_elapsed_seconds"]
                },
                "task_status":task_job.get_status(),
                "task_result": task_job.result,
                "task_errors":task_job.meta["errors"]
                }).dict()
        return resultdata

    def sendtask(self, q, exe, **kwargs):
        try:
            meta_template = self.get_redis_meta_template()
            task = self.local_queuedb[q]["queue"].enqueue_call(func=self.routes[exe], description=q, ttl=self.ttl,
                                                               result_ttl=self.task_result_ttl, kwargs=kwargs["kwargs"],
                                                               meta=meta_template, timeout=self.timeout)
            resultdata = self.render_task_response(task)
            return resultdata
        except Exception as e:
            return e

    def execute_task(self, method, **kwargs):
        try:
            kw = kwargs.get("kwargs", False)
            connectionargs = kw.get("connection_args", False)
            host = False
            if connectionargs:
                host = kw["connection_args"].get("host", False)
            queue_strategy = kw.get("queue_strategy", False)
            if queue_strategy == "pinned":
                self.check_and_create_q_w(hst=host)
                r = self.sendtask(q=host,exe=method,kwargs=kw)
            else:
                r = self.sendtask(q=config.redis_fifo_q,exe=method,kwargs=kw)
            return r
        except Exception as e:
            return e

    def fetchtask(self, task_id):
        log.info(f'fetching task: {task_id}')
        try:
            task = Job.fetch(task_id, connection=self.base_connection)
            response_object = self.render_task_response(task)
            status = response_object["data"]["task_status"]
            if "task_id" in str(response_object["data"]["task_result"]):
                for j in range(len(response_object["data"]["task_result"])):
                    tempres = Job.fetch(response_object["data"]["task_result"][j]["data"]["data"]["task_id"], connection=self.base_connection)
                    temprespobj = self.render_task_response(tempres)
                    if status != "started" or status != "queued":
                        if temprespobj["data"]["task_status"] == "started":
                            response_object["data"]["task_status"] = temprespobj["data"]["task_status"]
                    response_object["data"]["task_result"][j]["data"].update(temprespobj)
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
        log.info(f'getting jobs and status: {q}')
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
                #get startedjobs
                startedjobs = self.getstartedjobs(self.local_queuedb[q]["queue"])
                for job in startedjobs:
                    task.append(job)

                #get finishedjobs
                finishedjobs = self.getfinishedjobs(self.local_queuedb[q]["queue"])
                for job in finishedjobs:
                    task.append(job)

                #get failedjobs
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
        log.info(f'getting started jobs: {q}')
        try:
            registry = StartedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def getfinishedjobs(self, q):
        log.info(f'getting finished jobs: {q}')
        try:
            registry = FinishedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def getfailedjobs(self, q):
        log.info(f'getting failed jobs: {q}')
        try:
            registry = FailedJobRegistry(q, connection=self.base_connection)
            response_object = registry.get_job_ids()
            return response_object
        except Exception as e:
            return e

    def send_broadcast(self, msg: str):
        log.info(f'sending broadcast: {msg}')
        try:
            self.base_connection.publish(config.redis_broadcast_q, msg)
            return {
                'result': 'Message Sent'
            }

        except Exception as e:
            return e

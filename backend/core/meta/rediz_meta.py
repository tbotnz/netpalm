from rq import get_current_job
from datetime import datetime

from backend.core.models.task import model_response

def write_meta_error(data):
    job = get_current_job()
    job.meta["result"] = "failed"
    if type(data) == list:
        job.meta["errors"].append(data.split('\n'))
    else:
        job.meta["errors"].append(data)
    job.save_meta()

def prepare_netpalm_payload(job_result={}):
    try:
        job = get_current_job()
        resultdata = model_response(status="success",data={"task_id":job.id,"created_on":job.created_at.strftime("%Y-%m-%d %H:%M:%S.%f"),"task_queue":job.description,"task_status":"finished","task_result": job_result, "task_errors":job.meta["errors"]}).dict()
        return resultdata

    except Exception as e:
        return e
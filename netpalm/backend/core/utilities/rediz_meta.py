from rq import get_current_job

from netpalm.backend.core.models.task import Response


def write_meta_error(data):
    """custom exception handler for within an rpc job"""
    job = get_current_job()
    job.meta["result"] = "failed"
    if type(data) == list:
        job.meta["errors"].append(data.split('\n'))
    else:
        job.meta["errors"].append(data)
    job.save_meta()


def render_netpalm_payload(job_result={}):
    """in band rpc job result renderer"""
    try:
        job = get_current_job()
        resultdata = Response(status="success",
                              data={"task_id": job.id,
                                    "created_on": job.created_at.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                    "task_queue": job.description,
                                    "task_status": "finished",
                                    "task_result": job_result,
                                    "task_errors": job.meta["errors"]
                                    }).dict()
        return resultdata

    except Exception as e:
        return e

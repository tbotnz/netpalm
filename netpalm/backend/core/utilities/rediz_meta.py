import inspect
from logging import getLogger

from rq import get_current_job

from netpalm.backend.core.confload.confload import config
from netpalm.backend.core.models.task import Response
from netpalm.exceptions import NetpalmMetaProcessedException

log = getLogger(__name__)


def exception_full_name(exception: BaseException):
    name = exception.__class__.__name__
    if (module := inspect.getmodule(exception)) is None:
        return name

    name = f'{module.__name__}.{name}'
    return name


def yield_exception_chain(exc: BaseException):
    yield exc
    if exc.__context__ is None:
        return
    yield from yield_exception_chain(exc.__context__)


def write_meta_error(exception: Exception):
    """custom exception handler for within an rpc job"""
    if isinstance(exception, NetpalmMetaProcessedException):
        raise exception from None  # Don't process the same exception twice

    log.exception('`write_meta_error` processing error')

    job = get_current_job()
    job.meta["result"] = "failed"

    exception_chain = yield_exception_chain(exception)

    for exception in reversed(list(exception_chain)):
        task_error = {
            'exception_class': exception_full_name(exception),
            'exception_args': [arg for arg in exception.args if arg is not None]
        }
        job.meta["errors"].append(task_error)

    job.save_meta()
    raise NetpalmMetaProcessedException from exception


def write_meta_error_string(data):
    """custom exception handler for within an rpc job"""
    job = get_current_job()
    job.meta["result"] = "failed"
    job.meta["errors"].append(data)
    job.save_meta()
    raise Exception(f"failed: {data}")


def write_mandatory_meta():
    job = get_current_job()
    if job is None:  # it will be None in many/all unit tests
        return
    job.meta["assigned_worker"] = config.worker_name
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

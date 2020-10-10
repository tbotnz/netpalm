from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.models.task import Response, WorkerResponse
from netpalm.backend.core.models.models import PinnedStore

from netpalm.backend.core.redis import reds

router = APIRouter()


# get specific task
@router.get("/task/{task_id}", response_model=Response)
def get_task(task_id: str):
    try:
        r = reds.fetchtask(task_id=task_id)
        resp = jsonable_encoder(r)
        if not resp:
            raise HTTPException(status_code=404)
        return resp
    except Exception as e:
        raise HTTPException(status_code=404)

# get all tasks in queue
@router.get("/taskqueue/")
def get_task_list():
    try:
        r = reds.getjoblist(q=False)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


# task view route for specific host
@router.get("/taskqueue/{host}")
def get_host_task_list(host: str):
    try:
        r = reds.getjobliststatus(q=host)
        resp = jsonable_encoder(r)
        if not resp:
            raise HTTPException(status_code=404)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


# get all running workers
@router.get("/workers/", response_model=List[WorkerResponse])
def list_workers():
    try:
        r = reds.get_workers()
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


# get all running workers
@router.post("/workers/kill/{name}")
def kill_worker(name: str):
    try:
        r = reds.kill_worker(worker_name=name)
        resp = jsonable_encoder(r)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


# get the container process totals
@router.get("/containers/pinned/", response_model=List)
def list_pinned_containers():
    try:
        r = reds.fetch_pinned_store()
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


# # purge the container a container from the db
# @router.delete("/containers/pinned/{hostname}")
# def purge_pinned_containers_from_db(hostname: str):
#     try:
#         reds.purge_container_from_pinned_store(hostname)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e).split('\n'))

# # deregister worker
# @router.post("/containers/deregister/{hostname}")
# def deregister_workers_from_container(hostname: str):
#     try:
#         reds.deregister_worker(hostname)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e).split('\n'))
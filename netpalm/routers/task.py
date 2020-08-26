from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.models.task import Response, WorkerResponse
from netpalm.backend.core.redis import reds

router = APIRouter()

# get specific task 
@router.get("/task/{task_id}", response_model=Response)
def get_task(task_id: str):
    try:
        r = reds.fetchtask(task_id=task_id)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#get all tasks in queue
@router.get("/taskqueue/")
def get_task_list():
    try:
        r = reds.getjoblist(q=False)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#task view route for specific host
@router.get("/taskqueue/{host}")
def get_host_task_list(host: str):
    try:
        r = reds.getjobliststatus(q=host)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

#get all running workers
@router.get("/workers/", response_model=List[WorkerResponse])
def get_workers():
    try:
        r = reds.get_workers()
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))
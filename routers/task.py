from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds

from backend.core.models.task import model_response

router = APIRouter()

# get specific task 
@router.get("/task/{task_id}", response_model=model_response)
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

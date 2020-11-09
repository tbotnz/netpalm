from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

from netpalm.backend.core.models.task import ResponseBasic
from netpalm.backend.core.models.models import ScheduleInterval

from netpalm.backend.core.schedule import sched

router = APIRouter()


@router.get("/schedule/", response_model=ResponseBasic)
def get_scheduled_tasks_list():
    try:
        r = sched.get_scheduled_jobs()
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500)


@router.post("/schedule/{name}")
def add_scheduled_task(name: str, schedul: ScheduleInterval):
    try:
        data = schedul.dict(exclude_none=True)
        pl = data["schedule_payload"]
        del data["schedule_payload"]

        r = sched.add_netpalm_job(job_name=name,
                                  input_payload=pl,
                                  trigger="interval",
                                  trigger_args=data
                                  )
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.delete("/schedule/{id}", status_code=204)
def remove_scheduled_task(id: str):
    try:
        r = sched.remove_job(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split("\n"))

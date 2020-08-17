from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder

# load models
from backend.core.models.models import Script
from backend.core.models.task import Response
from backend.core.models.task import ResponseBasic
from backend.core.redis import reds
from backend.core.routes.routes import routes

router = APIRouter()


# get template list
@router.get("/script", response_model=ResponseBasic)
async def get_script_list():
    try:
        r = routes["ls"](fldr="script")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))


@router.post("/script", response_model=Response, status_code=201)
def execute_script(script: Script):
    try:
        req_data = script.dict()
        r = reds.execute_task(method="script", kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

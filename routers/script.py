
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds
from backend.core.routes.routes import routes

#load models
from backend.core.models.models import model_script
from backend.core.models.task import model_response
from backend.core.models.task import model_response_basic

router = APIRouter()

# get template list
@router.get("/script", response_model=model_response_basic)
async def get_script_list():
    try:
        r = routes["ls"](fldr="script")
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

@router.post("/script", response_model=model_response, status_code=201)
def execute_script(script: model_script):
    try:
        req_data = script.dict()
        r = reds.execute_task(method="script",kwargs=req_data)
        resp = jsonable_encoder(r)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e).split('\n'))

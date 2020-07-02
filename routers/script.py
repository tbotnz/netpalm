
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds

#load models
from backend.core.models.models import model_script, model_response

router = APIRouter()

@router.post("/script", response_model=model_response, status_code=201)
async def execute_script(script: model_script):
  try:
    req_data = script.dict()
    host = req_data.get("script", False)
    reds.check_and_create_q_w(hst=host)
    r = reds.sendtask(q=host,exe='script',kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass
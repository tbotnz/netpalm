
from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey

from backend.core.redis import reds

#load models
from backend.core.models.models import model_service
from backend.core.models.task import model_response

#load routes
from backend.core.routes.routes import routes

router = APIRouter()

@router.post("/service/{servicename}", response_model=model_response, status_code=201)
def execute_service(servicename: str, service: model_service):
  try:
    req_data = service.dict()
    req_data["netpalm_service_name"] = servicename
    r = reds.execute_task(method="render_service",kwargs=req_data)
    resp = jsonable_encoder(r)
    return resp
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e).split('\n'))
    pass
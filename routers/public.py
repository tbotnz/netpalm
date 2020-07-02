from fastapi import APIRouter, HTTPException, Depends

#load config
from backend.core.confload.confload import config

router = APIRouter()

#utility route - denied
@router.get("/denied")
async def denied():
  raise HTTPException(status_code=403, detail="forbidden")
from fastapi import APIRouter, HTTPException

#load config

router = APIRouter()

#utility route - denied
@router.get("/denied")
async def denied():
    raise HTTPException(status_code=403, detail="forbidden")
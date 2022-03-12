from typing import Optional, Any, List
from pydantic import BaseModel

class CustomScriptModel(BaseModel):
    args: Optional[str] = None

def run(payload: CustomScriptModel):
    try:
        # mandatory get of kwargs - payload comes through as {"kwargs": {"hello": "world"}}
        args = payload.args
        # reutn "world"
        return args
    except Exception as e:
        raise Exception(e)

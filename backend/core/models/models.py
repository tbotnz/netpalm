from typing import Optional, Set, Any
import typing
from pydantic import BaseModel

class model_j2config(BaseModel):
    template: str
    args: dict

class model_setconfig_args(BaseModel):
    payload: Optional[Any]
    target: Optional[str]
    config: Optional[str]
    uri: Optional[str]
    action: Optional[str]
    
class model_setconfig(BaseModel):
    library: str
    connection_args: dict
    config: Optional[Any]
    j2config: Optional[model_j2config]
    args: Optional[model_setconfig_args]

class model_script(BaseModel):
    script: str
    args: dict

class model_getconfig(BaseModel):
    library: str
    connection_args: dict
    command: Any
    args: Optional[dict]

class model_template_add(BaseModel):
    key: str
    driver: str
    command: str

class model_template_remove(BaseModel):
    template: str

class model_service(BaseModel):
    operation: str
    args: dict

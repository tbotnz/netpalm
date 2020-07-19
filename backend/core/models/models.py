from typing import Optional, Set, Any, Dict
import typing
from pydantic import BaseModel

class model_webhook(BaseModel):
    name: Optional[str] = None
    args: Optional[dict] = None
    j2template: Optional[str] = None

class model_j2config(BaseModel):
    template: str
    args: dict

class model_setconfig_args(BaseModel):
    payload: Optional[Any] = None
    target: Optional[str] = None
    config: Optional[str] = None
    uri: Optional[str] = None
    action: Optional[str] = None
    
class model_setconfig(BaseModel):
    library: str
    connection_args: dict
    config: Optional[Any] = None
    j2config: Optional[model_j2config] = None
    args: Optional[model_setconfig_args] = None
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[str] = None

class model_script(BaseModel):
    script: str
    args: Optional[dict] = None
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[str] = None

class model_getconfig(BaseModel):
    library: str
    connection_args: dict
    command: Any
    args: Optional[dict] = None
    webhook: Optional[model_webhook] = None
    queue_strategy: Optional[str] = None

class model_template_add(BaseModel):
    key: str
    driver: str
    command: str

class model_template_remove(BaseModel):
    template: str

class model_service(BaseModel):
    operation: str
    args: dict
    queue_strategy: Optional[str]

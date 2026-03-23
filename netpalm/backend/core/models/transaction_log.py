from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel


class TransactionLogEntryType(str, Enum):
    tfsm_pull = "TFSM_PULL"
    tfsm_delete = "TFSM_DELETE"
    tfsm_push = "TFSM_PUSH"
    unvrsl_tmp_push = "UNVRSL_PUSH"
    unvrsl_tmp_delete = "UNVRSL_DELETE"
    echo = "ECHO"
    init = "INITIALIZE"


class EchoModel(BaseModel):
    msg: str


class TFSMPullTemplateModel(BaseModel):
    key: str
    driver: str
    command: str


class TFSMPushTemplateModel(BaseModel):
    driver: str
    command: str
    template_text: str


class TFSMDeleteTemplateModel(BaseModel):
    fsm_template: str


class UniversalTemplatePushModel(BaseModel):
    """General template ingestor for handling base64 ingestion and writing"""

    route_type: str
    base64_payload: str
    name: str


class UniversalTemplateRemoveModel(BaseModel):
    """General template remover"""

    route_type: str
    name: Optional[str] = None


class InitEntryModel(BaseModel):
    init: Literal[True]


extn_update_types = {
    TransactionLogEntryType.tfsm_pull: TFSMPullTemplateModel,
    TransactionLogEntryType.tfsm_delete: TFSMDeleteTemplateModel,
    TransactionLogEntryType.tfsm_push: TFSMPushTemplateModel,
    TransactionLogEntryType.unvrsl_tmp_push: UniversalTemplatePushModel,
    TransactionLogEntryType.unvrsl_tmp_delete: UniversalTemplateRemoveModel,
    TransactionLogEntryType.init: InitEntryModel,
    TransactionLogEntryType.echo: EchoModel,
}


class TransactionLogEntryModel(BaseModel):
    seq: int
    type: TransactionLogEntryType
    data: Union[
        TFSMPullTemplateModel,
        TFSMDeleteTemplateModel,
        TFSMPushTemplateModel,
        EchoModel,
        InitEntryModel,
        UniversalTemplatePushModel,
        UniversalTemplateRemoveModel,
    ]

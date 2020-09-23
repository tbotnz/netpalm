from enum import Enum
from typing import Union, Literal

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


class UnivsersalTemplatePushModel(BaseModel):
    """general template ingest0r for handling base64 ingestion and writing"""
    route_type: str
    base64_payload: str
    name: str


class UnivsersalTemplateRemoveModel(BaseModel):
    """general template remover """
    route_type: str
    name: str = None


class InitEntryModel(BaseModel):
    init: Literal[True]  # only here to stop model from greedily matching literally any input


extn_update_types = {
    TransactionLogEntryType.tfsm_pull: TFSMPullTemplateModel,
    TransactionLogEntryType.tfsm_delete: TFSMDeleteTemplateModel,
    TransactionLogEntryType.tfsm_push: TFSMPushTemplateModel,
    TransactionLogEntryType.unvrsl_tmp_push: UnivsersalTemplatePushModel,
    TransactionLogEntryType.unvrsl_tmp_delete: UnivsersalTemplateRemoveModel,
    TransactionLogEntryType.init: InitEntryModel,
    TransactionLogEntryType.echo: EchoModel
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
                UnivsersalTemplatePushModel,
                UnivsersalTemplateRemoveModel
                ]

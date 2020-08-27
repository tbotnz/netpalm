from enum import Enum
from typing import Union, Literal

from pydantic import BaseModel


class TransactionLogEntryType(str, Enum):
    tfsm_pull = "TFSM_PULL"
    tfsm_delete = "TFSM_DELETE"
    tfsm_push = "TFSM_PUSH"
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


class InitEntryModel(BaseModel):
    init: Literal[True]  # only here to stop model from greedily matching literally any input


extn_update_types = {
    TransactionLogEntryType.tfsm_pull: TFSMPullTemplateModel,
    TransactionLogEntryType.tfsm_delete: TFSMDeleteTemplateModel,
    TransactionLogEntryType.tfsm_push: TFSMPushTemplateModel,
    TransactionLogEntryType.init: InitEntryModel,
    TransactionLogEntryType.echo: EchoModel
}


class TransactionLogEntryModel(BaseModel):
    seq: int
    type: TransactionLogEntryType
    data: Union[TFSMPullTemplateModel, TFSMDeleteTemplateModel, TFSMPushTemplateModel, EchoModel, InitEntryModel]

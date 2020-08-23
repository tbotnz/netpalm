from enum import Enum
from typing import Union, Literal

from pydantic import BaseModel


class TransactionLogEntryType(str, Enum):
    tfsm_pull = "TFSM_PULL"
    tfsm_delete = "TFSM_DELETE"
    echo = "ECHO"
    init = "INITIALIZE"


class EchoModel(BaseModel):
    msg: str


class TFSMPullTemplateModel(BaseModel):
    key: str
    driver: str
    command: str


class TFSMDeleteTemplateModel(BaseModel):
    fsm_template: str


class InitEntryModel(BaseModel):
    init: Literal[True]  # only here to stop model from greedily matching literally any input


extn_update_types = {
    TransactionLogEntryType.tfsm_pull: TFSMPullTemplateModel,
    TransactionLogEntryType.tfsm_delete: TFSMDeleteTemplateModel,
    TransactionLogEntryType.init: InitEntryModel,
    TransactionLogEntryType.echo: EchoModel
}


class TransactionLogEntryModel(BaseModel):
    seq: int
    type: TransactionLogEntryType
    data: Union[TFSMPullTemplateModel, TFSMDeleteTemplateModel, EchoModel, InitEntryModel]

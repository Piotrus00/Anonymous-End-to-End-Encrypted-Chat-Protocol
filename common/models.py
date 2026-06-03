"""Modele Pydantic dla ramek protokołu."""

from __future__ import annotations

from typing import Literal, TypeAlias

# noinspection PyUnresolvedReferences
from pydantic import BaseModel, ConfigDict, Field


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StatusPayload(ProtocolModel):
    status: str


class CiphertextPayload(ProtocolModel):
    ciphertext: str


class AckPayload(ProtocolModel):
    acked_msg_id: str


class ErrorFrame(ProtocolModel):
    type: Literal["ERROR"] = "ERROR"
    error_code: str
    details: str


class BaseMessageFrame(ProtocolModel):
    msg_id: str
    timestamp: int


class SessionMessageFrame(BaseMessageFrame):
    session_id: str


class InitFrame(BaseMessageFrame):
    type: Literal["INIT"] = "INIT"


class JoinFrame(SessionMessageFrame):
    type: Literal["JOIN"] = "JOIN"


class MsgFrame(SessionMessageFrame):
    type: Literal["MSG"] = "MSG"
    payload: CiphertextPayload


class AckFrame(SessionMessageFrame):
    type: Literal["ACK"] = "ACK"
    payload: AckPayload


class CloseRequestFrame(SessionMessageFrame):
    type: Literal["CLOSE"] = "CLOSE"


class CloseNoticeFrame(SessionMessageFrame):
    type: Literal["CLOSE"] = "CLOSE"
    payload: StatusPayload = Field(default_factory=lambda: StatusPayload(status="SESSION_CLOSED"))


class InitOkFrame(SessionMessageFrame):
    type: Literal["INIT_OK"] = "INIT_OK"
    payload: StatusPayload = Field(default_factory=lambda: StatusPayload(status="OK"))


class JoinOkFrame(SessionMessageFrame):
    type: Literal["JOIN_OK"] = "JOIN_OK"
    payload: StatusPayload = Field(default_factory=lambda: StatusPayload(status="OK"))


ProtocolMessage: TypeAlias = (
    InitFrame
    | JoinFrame
    | MsgFrame
    | AckFrame
    | CloseRequestFrame
    | CloseNoticeFrame
    | InitOkFrame
    | JoinOkFrame
    | ErrorFrame
)


"""Modele Pydantic dla ramek protokołu."""

from __future__ import annotations

from typing import Literal, TypeAlias

# noinspection PyUnresolvedReferences
from pydantic import BaseModel, ConfigDict, Field


class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid") # jeśli ktoś doda pole, którego nie ma w schemacie


#odrzucamy złe typy danych
class StatusPayload(ProtocolModel):
    status: str


class CiphertextPayload(ProtocolModel):
    ciphertext: str


class AckPayload(ProtocolModel):
    acked_msg_id: str


class KeyExchangePayload(ProtocolModel):
    public_key: str


class BaseMessageFrame(ProtocolModel):
    msg_id: str
    timestamp: int


class SessionMessageFrame(BaseMessageFrame):
    session_id: str


class AuthenticatedSessionFrame(SessionMessageFrame):
    """Ramki wymagające JWT (poza INIT i JOIN)."""
    token: str


#rodzaje wiadomości, które mogą być wysyłane w protokole
class InitFrame(BaseMessageFrame):
    type: Literal["INIT"] = "INIT"


class JoinFrame(SessionMessageFrame):
    type: Literal["JOIN"] = "JOIN"


class KeyExchangeFrame(AuthenticatedSessionFrame):
    type: Literal["KEY_EXCHANGE"] = "KEY_EXCHANGE"
    payload: KeyExchangePayload


class MsgFrame(AuthenticatedSessionFrame):
    type: Literal["MSG"] = "MSG"
    payload: CiphertextPayload


class AckFrame(AuthenticatedSessionFrame):
    type: Literal["ACK"] = "ACK"
    payload: AckPayload


class ErrorFrame(ProtocolModel):
    type: Literal["ERROR"] = "ERROR"
    error_code: str
    details: str


class CloseRequestFrame(AuthenticatedSessionFrame):
    type: Literal["CLOSE"] = "CLOSE"


class CloseNoticeFrame(SessionMessageFrame):
    type: Literal["CLOSE_NOTICE"] = "CLOSE_NOTICE"
    payload: StatusPayload = Field(default_factory=lambda: StatusPayload(status="SESSION_CLOSED"))


class InitOkFrame(SessionMessageFrame):
    type: Literal["INIT_OK"] = "INIT_OK"
    token: str
    payload: StatusPayload = Field(default_factory=lambda: StatusPayload(status="OK"))


class JoinOkFrame(SessionMessageFrame):
    type: Literal["JOIN_OK"] = "JOIN_OK"
    token: str | None = None  # tylko dla klienta, który dostaje nowy JWT (JOIN / INIT)
    payload: StatusPayload = Field(default_factory=lambda: StatusPayload(status="OK"))


#każda wiadomość, która może być wysłana w protokole, musi być jedną z tych typów
ProtocolMessage: TypeAlias = (
    InitFrame
    | JoinFrame
    | KeyExchangeFrame
    | MsgFrame
    | AckFrame
    | CloseRequestFrame
    | CloseNoticeFrame
    | InitOkFrame
    | JoinOkFrame
    | ErrorFrame
)

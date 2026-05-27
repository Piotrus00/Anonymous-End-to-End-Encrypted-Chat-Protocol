"""Wspólny moduł do enkodowania i dekodowania wiadomości JSON."""

from __future__ import annotations

import json
from typing import Annotated, Any, Tuple, TypeAlias

from pydantic import BaseModel, Field, RootModel, ValidationError

from .models import (
    AckFrame,
    CloseNoticeFrame,
    CloseRequestFrame,
    ErrorFrame,
    InitFrame,
    InitOkFrame,
    JoinFrame,
    JoinOkFrame,
    MsgFrame,
    PingFrame,
    PongFrame,
    ProtocolMessage,
)


IncomingDiscriminatedMessage: TypeAlias = (
    InitFrame
    | JoinFrame
    | MsgFrame
    | AckFrame
    | CloseNoticeFrame
    | InitOkFrame
    | JoinOkFrame
    | PingFrame
    | PongFrame
    | ErrorFrame
)


class MessageAdapter(RootModel):
    root: Annotated[IncomingDiscriminatedMessage, Field(discriminator="type")]


def decode_message(data: bytes) -> Tuple[bool, ProtocolMessage | None]:
    """
    Dekoduje wiadomość z bajtów i waliduje ją przez Pydantic.

    Returns:
        (success, message) - success True jeśli dekodowanie i walidacja się powiodły.
    """
    try:
        message_str = data.decode("utf-8")
        message_json = json.loads(message_str)
        obj = MessageAdapter.model_validate(message_json)
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError):
        return False, None

    if not isinstance(message_json, dict):
        return False, None

    message = obj.root

    # Rozróżniamy CLOSE request (bez payload) od CLOSE notice (z payload),
    # bo oba używają tego samego discriminatora "type".
    if isinstance(message, CloseNoticeFrame) and "payload" not in message_json:
        return (
            True,
            CloseRequestFrame(
                msg_id=message.msg_id,
                timestamp=message.timestamp,
                session_id=message.session_id,
            ),
        )

    return True, message


def encode_message(message: ProtocolMessage | BaseModel | dict[str, Any]) -> bytes:
    """Koduje model Pydantic albo słownik do JSON i dodaje znak nowej linii."""
    if isinstance(message, BaseModel):
        payload = message.model_dump(mode="json", exclude_none=True)
    else:
        payload = message
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

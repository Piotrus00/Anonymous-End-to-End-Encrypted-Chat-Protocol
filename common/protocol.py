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
    KeyExchangeFrame,
    MsgFrame,
    ProtocolMessage,
)


IncomingDiscriminatedMessage: TypeAlias = (
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


class MessageAdapter(RootModel):
    root: Annotated[IncomingDiscriminatedMessage, Field(discriminator="type")] # Field(discriminator="type") mówi Pydanticowi, żeby patrzył na pole "type"


def decode_message(data: bytes) -> Tuple[bool, ProtocolMessage | None]:
    """
    Dekoduje wiadomość z bajtów i waliduje ją przez Pydantic.

    Returns:
        (success, message) - success True jeśli dekodowanie i walidacja się powiodły.
    """
    try:
        message_str = data.decode("utf-8") # dekodujemy bajty do stringa
        message_json = json.loads(message_str) # parsujemy stringa do JSONa
        obj = MessageAdapter.model_validate(message_json) # walidujemy JSONa i mapujemy go na model Pydantic, wyżej dostępne modele
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError):
        return False, None

    if not isinstance(message_json, dict):
        return False, None

    return True, obj.root


def encode_message(message: ProtocolMessage | BaseModel | dict[str, Any]) -> bytes:
    """Koduje model Pydantic albo słownik do JSON i dodaje znak nowej linii."""
    if isinstance(message, BaseModel):
        payload = message.model_dump(mode="json", exclude_none=True)
    else:
        payload = message
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

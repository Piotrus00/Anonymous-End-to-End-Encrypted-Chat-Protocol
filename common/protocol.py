"""Wspólny moduł do enkodowania i dekodowania wiadomości JSON."""

from __future__ import annotations

import json
from typing import Any, Tuple

from pydantic import BaseModel, ValidationError

from .models import IncomingMessageModels, ProtocolMessage


def decode_message(data: bytes) -> Tuple[bool, ProtocolMessage | None]:
    """
    Dekoduje wiadomość z bajtów i waliduje ją przez Pydantic.

    Returns:
        (success, message) - success True jeśli dekodowanie i walidacja się powiodły.
    """
    try:
        message_str = data.decode("utf-8")
        message_json = json.loads(message_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, None

    for model in IncomingMessageModels:
        try:
            return True, model.model_validate(message_json)
        except ValidationError:
            continue

    return False, None


def encode_message(message: ProtocolMessage | BaseModel | dict[str, Any]) -> bytes:
    """Koduje model Pydantic albo słownik do JSON i dodaje znak nowej linii."""
    if isinstance(message, BaseModel):
        payload = message.model_dump(mode="json", exclude_none=True)
    else:
        payload = message
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

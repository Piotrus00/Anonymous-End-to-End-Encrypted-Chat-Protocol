"""JWT dla autoryzacji sesji — bez danych użytkownika (tylko sid + anonimowe pc)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

import jwt

from .config import JWT_ALGORITHM, JWT_EXPIRY_SECONDS, JWT_SECRET

# sid — identyfikator sesji protokołu
# pc  — losowy identyfikator uczestnika (participant credential), nie powiązany z użytkownikiem
CLAIM_SESSION_ID = "sid"
CLAIM_PARTICIPANT = "pc"


@dataclass(frozen=True)
class TokenClaims:
    session_id: str
    participant_credential: str


def new_participant_credential() -> str:
    """Losowy, anonimowy identyfikator slotu w sesji."""
    return uuid.uuid4().hex


def issue_session_token(session_id: str, participant_credential: str) -> str:
    """Podpisuje JWT zawierający wyłącznie sid i pc (bez danych użytkownika)."""
    now = int(time.time())
    payload = {
        CLAIM_SESSION_ID: session_id,
        CLAIM_PARTICIPANT: participant_credential,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validate_token(token: str) -> Tuple[bool, Optional[TokenClaims], str]:
    """
    Weryfikuje podpis i ważność JWT.

    Returns:
        (success, claims, error_detail)
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return False, None, "Token wygasl"
    except jwt.InvalidTokenError:
        return False, None, "Niepoprawny token"

    session_id = payload.get(CLAIM_SESSION_ID)
    participant_credential = payload.get(CLAIM_PARTICIPANT)
    if not session_id or not participant_credential:
        return False, None, "Token nie zawiera wymaganych pol sesji"

    return (
        True,
        TokenClaims(
            session_id=str(session_id),
            participant_credential=str(participant_credential),
        ),
        "",
    )

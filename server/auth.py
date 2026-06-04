from typing import Any, Optional

from common.errors import ERROR_INVALID_TOKEN
from common.jwt_auth import validate_token
from common.models import AuthenticatedSessionFrame, ErrorFrame
from .response_builder import error
from .session_manager import SessionManager


async def authorize_message(
    message_json: AuthenticatedSessionFrame,
    addr: tuple,
    session_manager: SessionManager,
) -> Optional[ErrorFrame]:
    """Waliduje JWT i zgodność z sesją klienta. Serwer nie odczytuje treści wiadomości."""
    token = message_json.token
    session_id = message_json.session_id

    valid, claims, detail = validate_token(token)
    if not valid or claims is None:
        return error(code=ERROR_INVALID_TOKEN, details=detail or "Niepoprawny token")

    if claims.session_id != session_id:
        return error(
            code=ERROR_INVALID_TOKEN,
            details="Token nie pasuje do session_id w wiadomosci",
        )

    authorized, reason = await session_manager.authorize_participant(
        addr, session_id, claims.participant_credential
    )
    if not authorized:
        return error(code=ERROR_INVALID_TOKEN, details=reason)

    return None


async def send_auth_error(writer: Any, auth_error: ErrorFrame) -> None:
    from common.protocol import encode_message

    await writer.send(encode_message(auth_error))

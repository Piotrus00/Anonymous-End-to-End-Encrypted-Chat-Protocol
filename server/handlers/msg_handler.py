import asyncio
from typing import Dict, Any

from ..response_builder import error
from common.errors import (
    ERROR_MISSING_FIELD,
    ERROR_PEER_NOT_CONNECTED,
    ERROR_DELIVERY_FAILED,
    ERROR_SESSION_NOT_FULL,
)
from ..session_manager import SessionManager

REQUIRED_MSG_FIELDS = ("type", "session_id", "msg_id", "timestamp")


async def handle_msg(
    message_json: Dict[str, Any],
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager: SessionManager,
    encode_message,
) -> None:
    missing_fields = [field for field in REQUIRED_MSG_FIELDS if field not in message_json]
    if missing_fields:
        response = error(
            code=ERROR_MISSING_FIELD,
            details=f"Brak wymaganych pol MSG: {', '.join(missing_fields)}",
        )
        writer.write(encode_message(response))
        await writer.drain()
        return

    msg_session_id = message_json.get("session_id")
    peer_writer = await session_manager.get_peer_writer(msg_session_id, addr)

    # If there is no peer writer, we cannot proceed.
    if peer_writer is None:
        # Check if the session is not full yet.
        session_participants = await session_manager.get_session(msg_session_id)
        if session_participants and len(session_participants) < 2:
            response = error(
                code=ERROR_SESSION_NOT_FULL,
                details="Nie mozna wyslac wiadomosci. Oczekiwanie na drugiego uzytkownika.",
            )
        # Otherwise, the peer must have disconnected.
        else:
            response = error(
                code=ERROR_PEER_NOT_CONNECTED,
                details="Drugi uczestnik sesji nie jest polaczony lub sesja jest nieprawidlowa.",
            )
        
        writer.write(encode_message(response))
        await writer.drain()
        return

    # If we have a peer_writer, try to send the message.
    try:
        peer_writer.write(encode_message(message_json))
        await peer_writer.drain()
        print(f"[MSG RELAY] {addr} -> session {msg_session_id}")
    except OSError:
        response = error(
            code=ERROR_DELIVERY_FAILED,
            details="Nie udalo sie dostarczyc wiadomosci do drugiego uzytkownika.",
        )
        writer.write(encode_message(response))
        await writer.drain()

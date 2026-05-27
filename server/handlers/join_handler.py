import asyncio
from typing import Dict, Any, Optional

from ..response_builder import join_ok, error
from common.errors import ERROR_MISSING_FIELD, ERROR_SESSION_INVALID
from ..session_manager import SessionManager


async def handle_join(
    message_json: Dict[str, Any],
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager: SessionManager,
    encode_message,
) -> Optional[str]:
    join_session_id = message_json.get("session_id")
    if not join_session_id:
        response = error(
            code=ERROR_MISSING_FIELD,
            details="Brak pola 'session_id' w JOIN",
        )
        writer.write(encode_message(response))
        await writer.drain()
        print(f"[JOIN FAIL] {addr} - brak session_id")
        return None

    joined, reason = await session_manager.join_session(join_session_id, addr)
    if not joined:
        response = error(code=ERROR_SESSION_INVALID, details=reason)
        writer.write(encode_message(response))
        await writer.drain()
        print(f"[JOIN FAIL] {addr} - {reason}")
        return None

    # --- Session is successfully joined ---
    print(f"[JOIN OK] {addr} dolaczyl do sesji {join_session_id}")

    # Send JOIN_OK to the joining client
    response_to_joiner = join_ok(
        session_id=join_session_id,
        msg_id=message_json.get("msg_id"),
        timestamp=message_json.get("timestamp"),
    )
    writer.write(encode_message(response_to_joiner))
    await writer.drain()

    # If the session is now full, notify the other participant
    session_participants = await session_manager.get_session(join_session_id)
    if len(session_participants) == 2:
        peer_writer = await session_manager.get_peer_writer(join_session_id, addr)
        if peer_writer:
            print(f"[SYSTEM] Powiadamiam pierwszego klienta w sesji {join_session_id}")
            notification_to_peer = join_ok(
                session_id=join_session_id,
                msg_id="notification",
                timestamp=message_json.get("timestamp"),
            )
            try:
                peer_writer.write(encode_message(notification_to_peer))
                await peer_writer.drain()
            except OSError as e:
                print(f"[ERROR] Nie udalo sie powiadomic klienta: {e}")

    return join_session_id

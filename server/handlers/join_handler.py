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
    else:
        joined, reason = await session_manager.join_session(join_session_id, addr)
        if joined:
            response = join_ok(
                session_id=join_session_id,
                msg_id=message_json.get("msg_id"),
                timestamp=message_json.get("timestamp"),
            )
            writer.write(encode_message(response))
            await writer.drain()
            print(f"[JOIN OK] {addr} dolaczyl do sesji {join_session_id}")
            return join_session_id
        else:
            response = error(
                code=ERROR_SESSION_INVALID,
                details=reason,
            )
            writer.write(encode_message(response))
            await writer.drain()
            print(f"[JOIN FAIL] {addr} - {reason}")
            return None

import asyncio
from typing import Dict, Any

from ..response_builder import error
from common.errors import ERROR_MISSING_FIELD
from ..session_manager import SessionManager

REQUIRED_ACK_FIELDS = ("type", "session_id", "msg_id", "timestamp", "payload")


async def handle_ack(
    message_json: Dict[str, Any],
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager: SessionManager,
    encode_message,
) -> None:
    missing_fields = [field for field in REQUIRED_ACK_FIELDS if field not in message_json]
    if not missing_fields and "acked_msg_id" not in message_json.get("payload", {}):
        missing_fields.append("payload.acked_msg_id")

    if missing_fields:
        response = error(
            code=ERROR_MISSING_FIELD,
            details=f"Brak wymaganych pol ACK: {', '.join(missing_fields)}",
        )
        writer.write(encode_message(response))
        await writer.drain()
        return

    msg_session_id = message_json.get("session_id")
    peer_writer = await session_manager.get_peer_writer(msg_session_id, addr)
    if peer_writer is None:
        # Peer disconnected before ACK could be delivered
        return

    try:
        peer_writer.write(encode_message(message_json))
        await peer_writer.drain()
        print(f"[ACK RELAY] {addr} -> session {msg_session_id}")
    except OSError:
        pass  # Ignore delivery errors for ACKs

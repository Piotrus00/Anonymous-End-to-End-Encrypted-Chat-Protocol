import asyncio

from ..session_manager import SessionManager
from common.models import AckFrame
from common.protocol import encode_message


async def handle_ack(
    message_json: AckFrame,
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager: SessionManager,
) -> None:
    msg_session_id = message_json.session_id
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
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from server.response_builder import error
from common.errors import ERROR_MISSING_FIELD, ERROR_PEER_NOT_CONNECTED, ERROR_DELIVERY_FAILED

REQUIRED_ACK_FIELDS = ("type", "session_id", "msg_id", "timestamp", "payload")

def handle_ack(message_json: Dict[str, Any], addr: tuple, conn: object, session_manager, encode_message) -> None:
    missing_fields = [field for field in REQUIRED_ACK_FIELDS if field not in message_json]
    if not missing_fields and "acked_msg_id" not in message_json.get("payload", {}):
        missing_fields.append("payload.acked_msg_id")

    if missing_fields:
        response = error(
            code=ERROR_MISSING_FIELD,
            details=f"Brak wymaganych pol ACK: {', '.join(missing_fields)}",
        )
        conn.sendall(encode_message(response))
        return

    msg_session_id = message_json.get("session_id")
    peer_conn = session_manager.get_peer_connection(msg_session_id, addr)
    if peer_conn is None:
        # Peer disconnected before ACK could be delivered
        return

    try:
        peer_conn.sendall(encode_message(message_json))
        print(f"[ACK RELAY] {addr} -> session {msg_session_id}")
    except OSError:
        pass # Ignore delivery errors for ACKs

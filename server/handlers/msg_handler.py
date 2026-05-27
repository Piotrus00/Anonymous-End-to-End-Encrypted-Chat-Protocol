from typing import Dict, Any

from ..response_builder import error
from common.errors import ERROR_MISSING_FIELD, ERROR_PEER_NOT_CONNECTED, ERROR_DELIVERY_FAILED

REQUIRED_MSG_FIELDS = ("type", "session_id", "msg_id", "timestamp")

def handle_msg(message_json: Dict[str, Any], addr: tuple, conn: object, session_manager, encode_message) -> None:
    missing_fields = [field for field in REQUIRED_MSG_FIELDS if field not in message_json]
    if missing_fields:
        response = error(
            code=ERROR_MISSING_FIELD,
            details=f"Brak wymaganych pol MSG: {', '.join(missing_fields)}",
        )
        conn.sendall(encode_message(response))
        return

    msg_session_id = message_json.get("session_id")
    peer_conn = session_manager.get_peer_connection(msg_session_id, addr)
    if peer_conn is None:
        response = error(
            code=ERROR_PEER_NOT_CONNECTED,
            details="Drugi uczestnik sesji nie jest polaczony",
        )
        conn.sendall(encode_message(response))
        return

    try:
        peer_conn.sendall(encode_message(message_json))
        print(f"[MSG RELAY] {addr} -> session {msg_session_id}")
    except OSError:
        response = error(
            code=ERROR_DELIVERY_FAILED,
            details="Nie udalo sie dostarczyc wiadomosci",
        )
        conn.sendall(encode_message(response))
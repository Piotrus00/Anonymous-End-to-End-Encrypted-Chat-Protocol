from typing import Dict, Any
from response_builder import close_notice, error

REQUIRED_CLOSE_FIELDS = ("type", "session_id", "msg_id", "timestamp")

def handle_close(message_json: Dict[str, Any], conn: object, session_manager, encode_message) -> bool:
    missing_fields = [field for field in REQUIRED_CLOSE_FIELDS if field not in message_json]
    if missing_fields:
        response = error(
            code="ERROR_MISSING_FIELD",
            details=f"Brak wymaganych pol CLOSE: {', '.join(missing_fields)}",
        )
        conn.sendall(encode_message(response))
        return False

    close_session_id = message_json.get("session_id")
    participants_conns = session_manager.close_session_and_get_connections(close_session_id)
    if not participants_conns:
        response = error(
            code="ERROR_SESSION_INVALID",
            details=f"Sesja {close_session_id} nie istnieje lub jest juz zamknieta",
        )
        conn.sendall(encode_message(response))
        return False

    notice = close_notice(
        session_id=close_session_id,
        msg_id=message_json.get("msg_id"),
        timestamp=message_json.get("timestamp"),
    )

    for participant_conn in participants_conns:
        try:
            participant_conn.sendall(encode_message(notice))
        except OSError:
            pass

    print(f"[CLOSE OK] Zamknieto sesje {close_session_id}")
    return True

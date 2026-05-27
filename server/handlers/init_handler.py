from typing import Dict, Any, Tuple
from response_builder import init_ok

def handle_init(message_json: Dict[str, Any], addr: tuple, conn: object, session_manager, encode_message) -> str:
    created_session_id = session_manager.create_session(addr)
    response = init_ok(
        session_id=created_session_id,
        msg_id=message_json.get("msg_id"),
        timestamp=message_json.get("timestamp"),
    )
    conn.sendall(encode_message(response))
    print(f"[INIT OK] Utworzona sesja {created_session_id} dla {addr}")
    return created_session_id

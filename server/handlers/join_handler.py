from typing import Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from server.response_builder import join_ok, error
from common.errors import ERROR_MISSING_FIELD, ERROR_SESSION_INVALID

def handle_join(message_json: Dict[str, Any], addr: tuple, conn: object, session_manager, encode_message) -> Optional[str]:
    join_session_id = message_json.get("session_id")
    if not join_session_id:
        response = error(
            code=ERROR_MISSING_FIELD,
            details="Brak pola 'session_id' w JOIN",
        )
        conn.sendall(encode_message(response))
        print(f"[JOIN FAIL] {addr} - brak session_id")
        return None
    else:
        joined, reason = session_manager.join_session(join_session_id, addr)
        if joined:
            response = join_ok(
                session_id=join_session_id,
                msg_id=message_json.get("msg_id"),
                timestamp=message_json.get("timestamp"),
            )
            conn.sendall(encode_message(response))
            print(f"[JOIN OK] {addr} dolaczyl do sesji {join_session_id}")
            return join_session_id
        else:
            response = error(
                code=ERROR_SESSION_INVALID,
                details=reason,
            )
            conn.sendall(encode_message(response))
            print(f"[JOIN FAIL] {addr} - {reason}")
            return None

import time
import uuid
from typing import Dict, Any, Tuple

def build_msg_frame(session_id: str, text: str) -> Tuple[str, Dict[str, Any]]:
    """Zwraca (msg_id, ramka)"""
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    frame = {
        "type": "MSG",
        "session_id": session_id,
        "msg_id": msg_id,
        "timestamp": int(time.time()),
        "payload": {"ciphertext": text},
    }
    return msg_id, frame

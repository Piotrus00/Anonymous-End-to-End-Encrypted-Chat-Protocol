import time
import uuid
from typing import Dict, Any

def build_ack_frame(session_id: str, acked_msg_id: str) -> Dict[str, Any]:
    """Zwraca slownik dla ramki ACK."""
    return {
        "type": "ACK",
        "session_id": session_id,
        "msg_id": f"ack_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
        "payload": {
            "acked_msg_id": acked_msg_id
        }
    }

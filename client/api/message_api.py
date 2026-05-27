import time
import uuid

def build_msg_frame(session_id: str, text: str) -> dict:
    return {
        "type": "MSG",
        "session_id": session_id,
        "msg_id": f"msg_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
        "payload": {"ciphertext": text},
    }

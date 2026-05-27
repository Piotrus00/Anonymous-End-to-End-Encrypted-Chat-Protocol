import time
import uuid

def build_pong_frame() -> dict:
    return {
        "type": "PONG",
        "msg_id": f"pong_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
    }

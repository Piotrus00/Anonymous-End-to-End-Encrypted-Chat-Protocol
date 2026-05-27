import time
import uuid

def build_close_frame(session_id: str) -> dict:
    return {
        "type": "CLOSE",
        "session_id": session_id,
        "msg_id": f"close_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
    }

def send_close(sock, session_id: str, encode_message) -> None:
    frame = build_close_frame(session_id)
    sock.sendall(encode_message(frame))

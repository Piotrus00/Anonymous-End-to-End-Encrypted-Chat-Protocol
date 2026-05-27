import time
import uuid
from common.models import AckFrame, AckPayload


def build_ack_frame(session_id: str, acked_msg_id: str) -> AckFrame:
    """Zwraca slownik dla ramki ACK."""
    return AckFrame(
        session_id=session_id,
        msg_id=f"ack_{uuid.uuid4().hex[:12]}",
        timestamp=int(time.time()),
        payload=AckPayload(acked_msg_id=acked_msg_id),
    )

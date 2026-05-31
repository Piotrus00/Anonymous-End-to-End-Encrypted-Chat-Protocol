import time
import uuid

from common.models import PongFrame


def build_pong_frame() -> PongFrame:
    return PongFrame(
        msg_id=f"pong_{uuid.uuid4().hex[:12]}",
        timestamp=int(time.time()),
    )

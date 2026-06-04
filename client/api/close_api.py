import time
import uuid
from typing import Any

from common.models import CloseRequestFrame
from common.protocol import encode_message


async def send_close(websocket: Any, session_id: str, token: str) -> None:
    frame = CloseRequestFrame(
        session_id=session_id,
        token=token,
        msg_id=f"close_{uuid.uuid4().hex[:12]}",
        timestamp=int(time.time()),
    )
    await websocket.send(encode_message(frame))

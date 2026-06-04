import time
import uuid
from typing import Any

from common.models import KeyExchangeFrame, KeyExchangePayload
from common.protocol import encode_message


def build_key_exchange_frame(session_id: str, token: str, public_key_b64: str) -> KeyExchangeFrame:
    return KeyExchangeFrame(
        session_id=session_id,
        token=token,
        msg_id=f"kex_{uuid.uuid4().hex[:12]}",
        timestamp=int(time.time()),
        payload=KeyExchangePayload(public_key=public_key_b64),
    )


async def send_key_exchange(
    websocket: Any,
    session_id: str,
    token: str,
    public_key_b64: str,
) -> None:
    frame = build_key_exchange_frame(session_id, token, public_key_b64)
    await websocket.send(encode_message(frame))

import asyncio
import time
import uuid

from common.models import CloseRequestFrame
from common.protocol import encode_message


async def send_close(writer: asyncio.StreamWriter, session_id: str) -> None:
    frame = CloseRequestFrame(
        session_id=session_id,
        msg_id=f"close_{uuid.uuid4().hex[:12]}",
        timestamp=int(time.time()),
    )
    writer.write(encode_message(frame))
    await writer.drain()

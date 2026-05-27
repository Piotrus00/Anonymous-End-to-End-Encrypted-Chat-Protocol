import asyncio
import time
from typing import Optional

from common.config import BUFFER_SIZE


async def send_init(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    encode_message,
    decode_message,
) -> Optional[str]:
    init_message = {
        "type": "INIT",
        "msg_id": "msg_001",
        "timestamp": int(time.time()),
    }

    print("\n-> Wysylam INIT...")
    writer.write(encode_message(init_message))
    await writer.drain()

    try:
        data = await reader.readuntil(b'\n')
    except asyncio.IncompleteReadError:
        print("X Serwer zamknal polaczenie")
        return None

    if not data:
        print("X Serwer zamknal polaczenie")
        return None

    success, response = decode_message(data)
    if not success or response.get("type") != "INIT_OK":
        details = response.get("details", "Niepoprawna odpowiedz serwera")
        print(f"X Blad: {details}")
        return None

    session_id = response.get("session_id")
    print(f"OK Sesja utworzona: {session_id}")
    return session_id

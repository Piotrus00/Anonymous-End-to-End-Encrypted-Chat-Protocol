import asyncio
import time
from typing import Optional

from common.models import InitFrame


async def send_init(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    encode_message,
    decode_message,
) -> Optional[str]:
    init_message = InitFrame(msg_id="msg_001", timestamp=int(time.time()))

    print("\n-> Wysylam INIT...")
    writer.write(encode_message(init_message))
    await writer.drain()

    try:
        data = await reader.readuntil(b'\n')
    except asyncio.LimitOverrunError as e:
        print("X Odpowiedz serwera przekroczyla dozwolony rozmiar")
        try:
            await reader.readexactly(e.consumed)
        except asyncio.IncompleteReadError:
            pass
        return None
    except asyncio.IncompleteReadError:
        print("X Serwer zamknal polaczenie")
        return None

    if not data:
        print("X Serwer zamknal polaczenie")
        return None

    success, response = decode_message(data)
    if not success or response is None or response.type != "INIT_OK":
        details = getattr(response, "details", "Niepoprawna odpowiedz serwera")
        print(f"X Blad: {details}")
        return None

    session_id = response.session_id
    print(f"OK Sesja utworzona: {session_id}")
    return session_id

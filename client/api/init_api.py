import time
from typing import Any, Optional

import websockets

from common.models import InitFrame
from common.protocol import encode_message, decode_message


async def send_init(websocket: Any) -> Optional[str]:
    init_message = InitFrame(msg_id="msg_001", timestamp=int(time.time()))

    print("\n-> Wysylam INIT...")
    await websocket.send(encode_message(init_message))

    try:
        data = await websocket.recv()
    except websockets.exceptions.PayloadTooBig:
        print("X Odpowiedz serwera przekroczyla dozwolony rozmiar")
        return None
    except websockets.exceptions.ConnectionClosed:
        print("X Serwer zamknal polaczenie")
        return None

    if not data:
        print("X Serwer zamknal polaczenie")
        return None

    if isinstance(data, str):
        data = data.encode("utf-8")

    success, response = decode_message(data)
    if not success or response is None or response.type != "INIT_OK":
        details = getattr(response, "details", "Niepoprawna odpowiedz serwera")
        print(f"X Blad: {details}")
        return None

    session_id = response.session_id
    print(f"OK Sesja utworzona: {session_id}")
    return session_id

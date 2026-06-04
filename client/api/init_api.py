import time
from typing import Any, Optional, Tuple

import websockets

from common.models import InitFrame
from common.protocol import encode_message, decode_message


async def send_init(websocket: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Wysyła INIT i zwraca (session_id, jwt_token).
    INIT nie wymaga tokenu w żądaniu.
    """
    init_message = InitFrame(msg_id="msg_001", timestamp=int(time.time()))

    print("\n-> Wysylam INIT...")
    await websocket.send(encode_message(init_message))

    try:
        data = await websocket.recv()
    except websockets.exceptions.PayloadTooBig:
        print("X Odpowiedz serwera przekroczyla dozwolony rozmiar")
        return None, None
    except websockets.exceptions.ConnectionClosed:
        print("X Serwer zamknal polaczenie")
        return None, None

    if not data:
        print("X Serwer zamknal polaczenie")
        return None, None

    if isinstance(data, str):
        data = data.encode("utf-8")

    success, response = decode_message(data.strip())
    if not success or response is None or response.type != "INIT_OK":
        details = getattr(response, "details", "Niepoprawna odpowiedz serwera")
        print(f"X Blad: {details}")
        return None, None

    session_id = response.session_id
    token = response.token
    print(f"OK Sesja utworzona: {session_id}")
    return session_id, token

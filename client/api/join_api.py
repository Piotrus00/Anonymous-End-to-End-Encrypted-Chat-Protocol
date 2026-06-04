import time
from typing import Any, Optional, Tuple

import websockets

from common.models import JoinFrame
from common.protocol import encode_message, decode_message


async def send_join(websocket: Any, session_id: str) -> Tuple[bool, Optional[str]]:
    """
    Wysyła JOIN i zwraca (sukces, jwt_token).
    JOIN nie wymaga tokenu w żądaniu.
    """
    join_message = JoinFrame(session_id=session_id, msg_id="msg_002", timestamp=int(time.time()))

    print(f"\n-> Wysylam JOIN dla sesji {session_id}...")
    await websocket.send(encode_message(join_message))

    try:
        data = await websocket.recv()
    except websockets.exceptions.PayloadTooBig:
        print("X Odpowiedz serwera przekroczyla dozwolony rozmiar")
        return False, None
    except websockets.exceptions.ConnectionClosed:
        print("X Serwer zamknal polaczenie")
        return False, None

    if not data:
        print("X Serwer zamknal polaczenie")
        return False, None

    if isinstance(data, str):
        data = data.encode("utf-8")

    success, response = decode_message(data.strip())
    if not success:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False, None

    if response is None:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False, None

    if response.type == "ERROR":
        print(f"X Blad serwera: {response.details}")
        return False, None

    if response.type != "JOIN_OK":
        print(f"X Blad: Oczekiwano JOIN_OK, otrzymano {response.type}")
        return False, None

    if not response.token:
        print("X Blad: Serwer nie zwrocil tokenu JWT")
        return False, None

    print(f"OK Dolaczono do sesji: {session_id}")
    return True, response.token

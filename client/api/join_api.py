import time
from typing import Any

import websockets

from common.models import JoinFrame
from common.protocol import encode_message, decode_message


async def send_join(websocket: Any, session_id: str) -> bool:
    join_message = JoinFrame(session_id=session_id, msg_id="msg_002", timestamp=int(time.time()))

    print(f"\n-> Wysylam JOIN dla sesji {session_id}...")
    await websocket.send(encode_message(join_message))

    try:
        data = await websocket.recv()
    except websockets.exceptions.PayloadTooBig:
        print("X Odpowiedz serwera przekroczyla dozwolony rozmiar")
        return False
    except websockets.exceptions.ConnectionClosed:
        print("X Serwer zamknal polaczenie")
        return False

    if not data:
        print("X Serwer zamknal polaczenie")
        return False

    if isinstance(data, str):
        data = data.encode("utf-8")

    success, response = decode_message(data)
    if not success:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False

    if response is None:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False

    if response.type == "ERROR":
        print(f"X Blad serwera: {response.details}")
        return False

    if response.type != "JOIN_OK":
        print(f"X Blad: Oczekiwano JOIN_OK, otrzymano {response.type}")
        return False

    print(f"OK Dolaczono do sesji: {session_id}")
    return True

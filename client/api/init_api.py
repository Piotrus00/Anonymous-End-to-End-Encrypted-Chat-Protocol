import time
from typing import Optional

from common.config import BUFFER_SIZE

def send_init(sock, encode_message, decode_message) -> Optional[str]:
    init_message = {
        "type": "INIT",
        "msg_id": "msg_001",
        "timestamp": int(time.time()),
    }

    print("\n-> Wysylam INIT...")
    sock.sendall(encode_message(init_message))

    data = sock.recv(BUFFER_SIZE)
    if not data:
        print("X Serwer zamknal polaczenie")
        return None

    success, response = decode_message(data)
    if not success or response.get("type") != "INIT":
        print("X Blad: Niepoprawna odpowiedz serwera")
        return None

    session_id = response.get("session_id")
    print(f"OK Sesja utworzona: {session_id}")
    return session_id
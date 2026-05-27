import time

from common.config import BUFFER_SIZE

def send_join(sock, session_id: str, encode_message, decode_message) -> bool:
    join_message = {
        "type": "JOIN",
        "session_id": session_id,
        "msg_id": "msg_002",
        "timestamp": int(time.time()),
    }

    print(f"\n-> Wysylam JOIN dla sesji {session_id}...")
    sock.sendall(encode_message(join_message))

    data = sock.recv(BUFFER_SIZE)
    if not data:
        print("X Serwer zamknal polaczenie")
        return False

    success, response = decode_message(data)
    if not success:
        print("X Blad: Niepoprawna odpowiedz serwera")
        return False

    if response.get("type") == "ERROR":
        print(f"X Blad serwera: {response.get('details', 'Nieznany blad')}")
        return False

    if response.get("type") != "JOIN":
        print(f"X Blad: Oczekiwano JOIN, otrzymano {response.get('type')}")
        return False

    print(f"OK Dolaczono do sesji: {session_id}")
    return True
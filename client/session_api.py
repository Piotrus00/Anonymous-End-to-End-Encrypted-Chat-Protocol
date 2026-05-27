import threading
import time
import uuid
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


def build_msg_frame(session_id: str, text: str) -> dict:
    return {
        "type": "MSG",
        "session_id": session_id,
        "msg_id": f"msg_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
        "payload": {"ciphertext": text},
    }


def build_close_frame(session_id: str) -> dict:
    return {
        "type": "CLOSE",
        "session_id": session_id,
        "msg_id": f"close_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
    }


def build_pong_frame() -> dict:
    return {
        "type": "PONG",
        "msg_id": f"pong_{uuid.uuid4().hex[:12]}",
        "timestamp": int(time.time()),
    }


def send_close(sock, session_id: str, encode_message) -> None:
    frame = build_close_frame(session_id)
    sock.sendall(encode_message(frame))


def start_receiver(sock, encode_message, decode_message) -> threading.Thread:
    def _receiver_loop():
        while True:
            try:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    break
                success, response = decode_message(data)
                if not success:
                    continue

                response_type = response.get("type")
                if response_type == "MSG":
                    payload = response.get("payload", {})
                    text = payload.get("ciphertext", "")
                    print(f"\n[MSG] {text}")
                elif response_type == "CLOSE":
                    closed_sid = response.get("session_id")
                    print(f"\n[CLOSE] Sesja {closed_sid} zostala zamknieta")
                    break
                elif response_type == "PING":
                    pong_frame = build_pong_frame()
                    sock.sendall(encode_message(pong_frame))
                elif response_type == "ERROR":
                    print(f"\n[ERROR] {response.get('details', 'Nieznany blad')}")
            except OSError:
                break

    thread = threading.Thread(target=_receiver_loop, daemon=True)
    thread.start()
    return thread


def chat_loop(sock, session_id: str, encode_message, decode_message) -> None:
    print("\nMozesz wysylac MSG. Wpisz 'exit' aby wyslac CLOSE i zakonczyc.")
    start_receiver(sock, encode_message, decode_message)

    while True:
        text = input("Ty: ").strip()
        if text.lower() == "exit":
            send_close(sock, session_id, encode_message)
            time.sleep(0.2)
            return
        if not text:
            continue

        frame = build_msg_frame(session_id, text)
        sock.sendall(encode_message(frame))

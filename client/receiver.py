import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.config import BUFFER_SIZE
from api.pong_api import build_pong_frame

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

import sys
import threading
import struct
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.protocol import read_exactly
from api.pong_api import build_pong_frame
from api.ack_api import build_ack_frame

def start_receiver(sock, encode_message, decode_message, unacked_messages: Dict[str, float], unacked_lock: threading.Lock) -> threading.Thread:
    def _receiver_loop():
        while True:
            try:
                # Etap 1: Odczytaj 4-bajtowy nagłówek z długością wiadomości
                header_bytes = read_exactly(sock, 4)
                if not header_bytes:
                    break
                
                message_length = struct.unpack('!I', header_bytes)[0]

                # Etap 2: Odczytaj właściwą wiadomość o zadeklarowanej długości
                data = read_exactly(sock, message_length)
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

                    # Send ACK
                    session_id = response.get("session_id")
                    msg_id = response.get("msg_id")
                    if session_id and msg_id:
                        ack_frame = build_ack_frame(session_id, msg_id)
                        sock.sendall(encode_message(ack_frame))

                elif response_type == "ACK":
                    payload = response.get("payload", {})
                    acked_msg_id = payload.get("acked_msg_id")
                    with unacked_lock:
                        if acked_msg_id in unacked_messages:
                            unacked_messages.pop(acked_msg_id, None)
                            print(f"\n[SYSTEM] Otrzymano potwierdzenie dla {acked_msg_id}")

                elif response_type == "CLOSE":
                    closed_sid = response.get("session_id")
                    print(f"\n[CLOSE] Sesja {closed_sid} zostala zamknieta")
                    break
                elif response_type == "PING":
                    pong_frame = build_pong_frame()
                    sock.sendall(encode_message(pong_frame))
                elif response_type == "ERROR":
                    print(f"\n[ERROR] {response.get('details', 'Nieznany blad')}")
            except (OSError, ConnectionError):
                break

    thread = threading.Thread(target=_receiver_loop, daemon=True)
    thread.start()
    return thread

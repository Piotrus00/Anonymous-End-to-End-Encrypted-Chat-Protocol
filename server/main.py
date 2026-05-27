import socket
import threading
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.protocol import decode_message, encode_message
from response_builder import ping

from client_handler import handle_client
from common.config import HOST, PORT, KEEP_ALIVE_INTERVAL
from session_manager import SessionManager

session_manager = SessionManager()


def keep_alive_loop(manager: SessionManager, encode_message_func):
    while True:
        time.sleep(KEEP_ALIVE_INTERVAL)
        with manager.lock:
            for client_addr, status in list(manager.client_status.items()):
                if time.time() - status["last_activity_time"] > KEEP_ALIVE_INTERVAL:
                    conn = manager.connections.get(client_addr)
                    if conn:
                        try:
                            ping_message = ping(msg_id="ping_123", timestamp=int(time.time()))
                            conn.sendall(encode_message_func(ping_message))
                            manager.increment_missed_pings(client_addr)
                            print(f"[PING] Wyslano PING do {client_addr}")
                        except OSError:
                            pass


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[START] Serwer nasluchuje na {HOST}:{PORT}")

        keep_alive_thread = threading.Thread(
            target=keep_alive_loop,
            args=(session_manager, encode_message),
            daemon=True,
        )
        keep_alive_thread.start()

        try:
            while True:
                conn, addr = s.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, session_manager, decode_message, encode_message),
                    daemon=True,
                )
                thread.start()
                print(f"[AKTYWNE] Watki: {threading.active_count() - 2}")
        except KeyboardInterrupt:
            print("\n[STOP] Serwer zatrzymywany...")


if __name__ == "__main__":
    main()

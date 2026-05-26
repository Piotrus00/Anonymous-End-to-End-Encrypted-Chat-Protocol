import socket
import threading
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.protocol import decode_message, encode_message

from client_handler import handle_client
from common.config import HOST, PORT
from session_manager import SessionManager

session_manager = SessionManager()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[START] Serwer nasluchuje na {HOST}:{PORT}")

        try:
            while True:
                conn, addr = s.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, session_manager, decode_message, encode_message),
                    daemon=True,
                )
                thread.start()
                print(f"[AKTYWNE] Watki: {threading.active_count() - 1}")
        except KeyboardInterrupt:
            print("\n[STOP] Serwer zatrzymywany...")


if __name__ == "__main__":
    main()
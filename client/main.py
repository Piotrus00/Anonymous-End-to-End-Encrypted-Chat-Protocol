import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.protocol import decode_message, encode_message

from common.config import HOST, PORT
from session_api import chat_loop, send_init, send_join


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Polaczono z serwerem!")

        print("\n[1] Tworzyc nowa sesje (INIT)")
        print("[2] Dolaczyc do istniejacej sesji (JOIN)")
        choice = input("\nWybierz opcje (1 lub 2): ").strip()

        if choice == "1":
            session_id = send_init(s, encode_message, decode_message)
            if not session_id:
                return
            print(f"\nPrzekaz session_id drugiemu uzytkownikowi: {session_id}")
            chat_loop(s, session_id, encode_message, decode_message)
            return

        if choice == "2":
            session_id = input("Wpisz session_id sesji, do ktorej chcesz dolaczyc: ").strip()
            if not session_id:
                print("X session_id nie moze byc pusty")
                return
            if not send_join(s, session_id, encode_message, decode_message):
                return
            chat_loop(s, session_id, encode_message, decode_message)
            return

        print("X Niepoprawny wybor")


if __name__ == "__main__":
    main()
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.protocol import decode_message, encode_message
from common.config import HOST, PORT
from api.init_api import send_init
from api.join_api import send_join
from api.message_api import build_msg_frame
from api.close_api import send_close
from receiver import start_receiver

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

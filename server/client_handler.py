from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.config import BUFFER_SIZE, MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from common.errors import ERROR_BAD_JSON, ERROR_MESSAGE_TOO_LARGE, ERROR_RATE_LIMIT_EXCEEDED
from response_builder import error
from message_dispatcher import dispatch

def handle_client(conn, addr, session_manager, decode_message, encode_message) -> None:
    print(f"[NOWE POLACZENIE] Polaczono z {addr}")
    session_id: Optional[str] = None
    session_manager.register_connection(addr, conn)

    with conn:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break

                if len(data) > MAX_MESSAGE_SIZE:
                    print(f"[{addr}] Odrzucono wiadomosc: przekroczono rozmiar ({len(data)} bajtow)")
                    response = error(
                        code=ERROR_MESSAGE_TOO_LARGE,
                        details="Wiadomosc jest zbyt duza",
                    )
                    conn.sendall(encode_message(response))
                    break

                if not session_manager.check_and_update_rate_limit(addr, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW):
                    print(f"[{addr}] Przekroczono limit wiadomosci. Odrzucono.")
                    response = error(
                        code=ERROR_RATE_LIMIT_EXCEEDED,
                        details="Wysylasz wiadomosci zbyt szybko. Zwolnij.",
                    )
                    conn.sendall(encode_message(response))
                    continue

                success, message_json = decode_message(data)
                if not success:
                    print(f"[{addr}] Blad: Otrzymano niepoprawny JSON")
                    response = error(
                        code=ERROR_BAD_JSON,
                        details="Niepoprawny format wiadomosci JSON",
                    )
                    conn.sendall(encode_message(response))
                    continue

                session_manager.update_client_activity(addr)

                print(f"[{addr}] Otrzymano: {message_json}")

                result = dispatch(message_json, addr, conn, session_manager, encode_message)
                
                if result == "CLOSE":
                    break
                elif result is not None:
                    session_id = result

            except ConnectionResetError:
                break

    if session_id:
        session_manager.remove_from_session(addr, session_id)

    session_manager.unregister_connection(addr)
    if session_id:
        print(f"[ROZLACZONO] {addr} (sesja: {session_id})")
    else:
        print(f"[ROZLACZONO] {addr}")

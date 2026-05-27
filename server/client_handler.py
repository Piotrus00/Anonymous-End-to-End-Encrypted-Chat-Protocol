from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.config import BUFFER_SIZE
from common.errors import ERROR_BAD_JSON
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

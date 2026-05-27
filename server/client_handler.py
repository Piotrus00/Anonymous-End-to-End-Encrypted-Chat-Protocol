from typing import Optional

from common.config import BUFFER_SIZE
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
                    break

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

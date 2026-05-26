from typing import Optional

from config import BUFFER_SIZE
from response_builder import error, init_ok, join_ok


def handle_client(conn, addr, session_manager, decode_message, encode_message) -> None:
    print(f"[NOWE POŁĄCZENIE] Połączono z {addr}")
    session_id: Optional[str] = None

    with conn:
        while True:
            try:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break

                success, message_json = decode_message(data)
                if not success:
                    print(f"[{addr}] Błąd: Otrzymano niepoprawny JSON")
                    break

                message_type = message_json.get("type")
                print(f"[{addr}] Otrzymano: {message_json}")

                if message_type == "INIT":
                    created_session_id = session_manager.create_session(addr)
                    session_id = created_session_id
                    response = init_ok(
                        session_id=created_session_id,
                        msg_id=message_json.get("msg_id"),
                        timestamp=message_json.get("timestamp"),
                    )
                    print(f"[INIT OK] Utworzona sesja {created_session_id} dla {addr}")

                elif message_type == "JOIN":
                    join_session_id = message_json.get("session_id")
                    if not join_session_id:
                        response = error(
                            code="ERROR_MISSING_FIELD",
                            details="Brak pola 'session_id' w JOIN",
                        )
                        print(f"[JOIN FAIL] {addr} - brak session_id")
                    else:
                        joined, reason = session_manager.join_session(join_session_id, addr)
                        if joined:
                            session_id = join_session_id
                            response = join_ok(
                                session_id=join_session_id,
                                msg_id=message_json.get("msg_id"),
                                timestamp=message_json.get("timestamp"),
                            )
                            print(f"[JOIN OK] {addr} dolaczyl do sesji {join_session_id}")
                        else:
                            response = error(
                                code="ERROR_SESSION_INVALID",
                                details=reason,
                            )
                            print(f"[JOIN FAIL] {addr} - {reason}")

                else:
                    response = error(
                        code="ERROR_UNKNOWN_TYPE",
                        details=f"Nieznany typ wiadomości: {message_type}",
                    )

                conn.sendall(encode_message(response))

            except ConnectionResetError:
                break

    if session_id:
        print(f"[ROZŁĄCZONO] {addr} (sesja: {session_id})")
    else:
        print(f"[ROZŁĄCZONO] {addr}")



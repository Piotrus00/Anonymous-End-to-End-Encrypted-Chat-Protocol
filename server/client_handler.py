from typing import Optional

from config import BUFFER_SIZE
from response_builder import error, init_ok, join_ok

REQUIRED_MSG_FIELDS = ("type", "session_id", "msg_id", "timestamp")


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
                    conn.sendall(encode_message(response))
                    print(f"[INIT OK] Utworzona sesja {created_session_id} dla {addr}")

                elif message_type == "JOIN":
                    join_session_id = message_json.get("session_id")
                    if not join_session_id:
                        response = error(
                            code="ERROR_MISSING_FIELD",
                            details="Brak pola 'session_id' w JOIN",
                        )
                        conn.sendall(encode_message(response))
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
                            conn.sendall(encode_message(response))
                            print(f"[JOIN OK] {addr} dolaczyl do sesji {join_session_id}")
                        else:
                            response = error(
                                code="ERROR_SESSION_INVALID",
                                details=reason,
                            )
                            conn.sendall(encode_message(response))
                            print(f"[JOIN FAIL] {addr} - {reason}")

                elif message_type == "MSG":
                    missing_fields = [field for field in REQUIRED_MSG_FIELDS if field not in message_json]
                    if missing_fields:
                        response = error(
                            code="ERROR_MISSING_FIELD",
                            details=f"Brak wymaganych pol MSG: {', '.join(missing_fields)}",
                        )
                        conn.sendall(encode_message(response))
                        continue

                    msg_session_id = message_json.get("session_id")
                    peer_conn = session_manager.get_peer_connection(msg_session_id, addr)
                    if peer_conn is None:
                        response = error(
                            code="ERROR_PEER_NOT_CONNECTED",
                            details="Drugi uczestnik sesji nie jest polaczony",
                        )
                        conn.sendall(encode_message(response))
                        continue

                    try:
                        peer_conn.sendall(encode_message(message_json))
                        print(f"[MSG RELAY] {addr} -> session {msg_session_id}")
                    except OSError:
                        response = error(
                            code="ERROR_DELIVERY_FAILED",
                            details="Nie udalo sie dostarczyc wiadomosci",
                        )
                        conn.sendall(encode_message(response))

                else:
                    response = error(
                        code="ERROR_UNKNOWN_TYPE",
                        details=f"Nieznany typ wiadomosci: {message_type}",
                    )
                    conn.sendall(encode_message(response))

            except ConnectionResetError:
                break

    session_manager.unregister_connection(addr)
    if session_id:
        print(f"[ROZLACZONO] {addr} (sesja: {session_id})")
    else:
        print(f"[ROZLACZONO] {addr}")

from typing import Any, Optional

import websockets

from common.config import MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from common.errors import (
    ERROR_BAD_JSON,
    ERROR_DISCONNECTED,
    ERROR_MESSAGE_TOO_LARGE,
    ERROR_RATE_LIMIT_EXCEEDED,
)
from .response_builder import error
from .message_dispatcher import dispatch
from .session_manager import SessionManager
from common.protocol import decode_message, encode_message


async def handle_client(
    websocket: Any,
    path: Optional[str] = None,
    session_manager: Optional[SessionManager] = None,
) -> None:
    if session_manager is None:
        raise RuntimeError("SessionManager is required")

    addr = websocket.remote_address or ("unknown", id(websocket))
    print(f"[NOWE POLACZENIE] Polaczono z {addr}")
    await session_manager.register_connection(addr, websocket)

    closed_by_protocol = False

    try:
        while True:
            try:
                message = await websocket.recv() # Odbierz wiadomość od klienta
                
            except websockets.exceptions.PayloadTooBig:
                print(f"[{addr}] Odrzucono wiadomosc: przekroczono rozmiar ramki")
                response = error(
                    code=ERROR_MESSAGE_TOO_LARGE,
                    details="Wiadomosc jest zbyt duza",
                )
                await websocket.send(encode_message(response))
                break
            except websockets.exceptions.ConnectionClosed:
                break

            if isinstance(message, str):
                message_bytes = message.encode("utf-8")
            else:
                message_bytes = message

            if len(message_bytes) > MAX_MESSAGE_SIZE:
                print(f"[{addr}] Odrzucono wiadomosc: przekroczono rozmiar ({len(message_bytes)} bajtow)")
                response = error(
                    code=ERROR_MESSAGE_TOO_LARGE,
                    details="Wiadomosc jest zbyt duza",
                )
                await websocket.send(encode_message(response))
                continue

            # Sprawdź limit wiadomości dla tego klienta
            if not await session_manager.check_and_update_rate_limit(addr, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW):
                print(f"[{addr}] Przekroczono limit wiadomosci. Odrzucono.")
                response = error(
                    code=ERROR_RATE_LIMIT_EXCEEDED,
                    details="Wysylasz wiadomosci zbyt szybko. Zwolnij.",
                )
                await websocket.send(encode_message(response))
                continue

            success, message_json = decode_message(message_bytes.strip()) # Odkoduj otrzymaną wiadomość + sprawdź poprawność
            if not success:
                print(f"[{addr}] Blad: Otrzymano niepoprawny JSON")
                response = error(
                    code=ERROR_BAD_JSON,
                    details="Niepoprawny format wiadomosci JSON",
                )
                await websocket.send(encode_message(response)) # Odpowiedz klientowi, że otrzymany JSON jest niepoprawny
                continue

            await session_manager.update_client_activity(addr) # Zaktualizuj timestamp ostatniej aktywności klienta, aby monitorować połączenie i ewentualnie rozłączyć nieaktywnych klientów

            print(f"[{addr}] Otrzymano: {message_json}")

            result = await dispatch(message_json, addr, websocket, session_manager)

            if result == "CLOSE":
                closed_by_protocol = True
                break

    except Exception as e:
        print(f"[{addr}] Niespodziewany blad: {e}")
    finally:
        if not closed_by_protocol:
        # Jeśli klient rozłączył się niespodziewanie, spróbuj powiadomić drugiego uczestnika sesji o rozłączeniu,
        #  wysyłając mu ramkę ERROR z odpowiednim kodem i komunikatem
            session_id = await session_manager.find_session_by_addr(addr)
            if session_id:
                peer_writer = await session_manager.get_peer_writer(session_id, addr)
                if peer_writer:
                    try:
                        error_message = error(
                            code=ERROR_DISCONNECTED,
                            details="Drugi uczestnik utracil polaczenie.",
                        )
                        await peer_writer.send(encode_message(error_message))
                    except (ConnectionError, OSError, websockets.exceptions.ConnectionClosed):
                        pass
        print(f"[ROZLACZONO] {addr}")
        await session_manager.disconnect_client(addr)
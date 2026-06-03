from typing import Any

import websockets

from common.config import MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from common.errors import ERROR_BAD_JSON, ERROR_MESSAGE_TOO_LARGE, ERROR_RATE_LIMIT_EXCEEDED
from .response_builder import error
from .message_dispatcher import dispatch
from .session_manager import SessionManager
from common.protocol import decode_message, encode_message


async def handle_client(
    websocket: Any,
    path: str,
    session_manager: SessionManager,
) -> None:
    addr = websocket.remote_address or ("unknown", id(websocket))
    print(f"[NOWE POLACZENIE] Polaczono z {addr}")
    await session_manager.register_connection(addr, websocket)

    try:
        while True:
            try:
                message = await websocket.recv()
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

            if not await session_manager.check_and_update_rate_limit(addr, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW):
                print(f"[{addr}] Przekroczono limit wiadomosci. Odrzucono.")
                response = error(
                    code=ERROR_RATE_LIMIT_EXCEEDED,
                    details="Wysylasz wiadomosci zbyt szybko. Zwolnij.",
                )
                await websocket.send(encode_message(response))
                continue

            success, message_json = decode_message(message_bytes.strip())
            if not success:
                print(f"[{addr}] Blad: Otrzymano niepoprawny JSON")
                response = error(
                    code=ERROR_BAD_JSON,
                    details="Niepoprawny format wiadomosci JSON",
                )
                await websocket.send(encode_message(response))
                continue

            await session_manager.update_client_activity(addr)

            print(f"[{addr}] Otrzymano: {message_json}")

            result = await dispatch(message_json, addr, websocket, session_manager)

            if result == "CLOSE":
                break

    except Exception as e:
        print(f"[{addr}] Niespodziewany blad: {e}")
    finally:
        print(f"[ROZLACZONO] {addr}")
        await session_manager.disconnect_client(addr)
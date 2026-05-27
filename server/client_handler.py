import asyncio
from typing import Optional

from common.config import MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from common.errors import ERROR_BAD_JSON, ERROR_MESSAGE_TOO_LARGE, ERROR_RATE_LIMIT_EXCEEDED
from .response_builder import error
from .message_dispatcher import dispatch
from .session_manager import SessionManager


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    session_manager: SessionManager,
    decode_message,
    encode_message,
) -> None:
    addr = writer.get_extra_info("peername")
    print(f"[NOWE POLACZENIE] Polaczono z {addr}")
    session_id: Optional[str] = None
    await session_manager.register_connection(addr, writer)

    try:
        while True:
            try:
                message_bytes = await reader.readuntil(b'\n')
            except asyncio.IncompleteReadError:
                # Client disconnected cleanly
                break

            if len(message_bytes) > MAX_MESSAGE_SIZE:
                print(f"[{addr}] Odrzucono wiadomosc: przekroczono rozmiar ({len(message_bytes)} bajtow)")
                response = error(
                    code=ERROR_MESSAGE_TOO_LARGE,
                    details="Wiadomosc jest zbyt duza",
                )
                writer.write(encode_message(response))
                await writer.drain()
                continue

            if not await session_manager.check_and_update_rate_limit(addr, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW):
                print(f"[{addr}] Przekroczono limit wiadomosci. Odrzucono.")
                response = error(
                    code=ERROR_RATE_LIMIT_EXCEEDED,
                    details="Wysylasz wiadomosci zbyt szybko. Zwolnij.",
                )
                writer.write(encode_message(response))
                await writer.drain()
                continue

            success, message_json = decode_message(message_bytes.strip())
            if not success:
                print(f"[{addr}] Blad: Otrzymano niepoprawny JSON")
                response = error(
                    code=ERROR_BAD_JSON,
                    details="Niepoprawny format wiadomosci JSON",
                )
                writer.write(encode_message(response))
                await writer.drain()
                continue

            await session_manager.update_client_activity(addr)

            print(f"[{addr}] Otrzymano: {message_json}")

            result = await dispatch(message_json, addr, writer, session_manager, encode_message)

            if result == "CLOSE":
                break
            # If dispatch returns a session_id, store it but continue the loop
            elif result is not None and result != "CLOSE":
                session_id = result

    except (ConnectionResetError, ConnectionError):
        print(f"[{addr}] Blad polaczenia.")
    finally:
        if session_id:
            await session_manager.remove_from_session(addr, session_id)

        await session_manager.unregister_connection(addr)
        if writer:
            writer.close()
            await writer.wait_closed()

        if session_id:
            print(f"[ROZLACZONO] {addr} (sesja: {session_id})")
        else:
            print(f"[ROZLACZONO] {addr}")

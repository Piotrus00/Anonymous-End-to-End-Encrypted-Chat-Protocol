from typing import Any

import websockets

from ..response_builder import error
from common.errors import (
    ERROR_DELIVERY_FAILED,
    ERROR_PEER_NOT_CONNECTED,
    ERROR_SESSION_NOT_FULL,
)
from ..session_manager import SessionManager
from common.models import KeyExchangeFrame
from common.protocol import encode_message


async def handle_key_exchange(
    message_json: KeyExchangeFrame,
    addr: tuple,
    writer: Any,
    session_manager: SessionManager,
) -> None:
    """Przekazuje KEY_EXCHANGE do peer-a bez odczytywania klucza publicznego."""
    session_id = message_json.session_id
    peer_writer = await session_manager.get_peer_writer(session_id, addr)

    if peer_writer is None:
        session_participants = await session_manager.get_session(session_id)
        if session_participants and len(session_participants) < 2:
            response = error(
                code=ERROR_SESSION_NOT_FULL,
                details="Nie mozna wymienic kluczy. Oczekiwanie na drugiego uzytkownika.",
            )
        else:
            response = error(
                code=ERROR_PEER_NOT_CONNECTED,
                details="Drugi uczestnik sesji nie jest polaczony lub sesja jest nieprawidlowa.",
            )
        await writer.send(encode_message(response))
        return

    try:
        await peer_writer.send(encode_message(message_json))
        print(f"[KEY_EXCHANGE RELAY] {addr} -> session {session_id}")
    except (OSError, websockets.exceptions.ConnectionClosed):
        response = error(
            code=ERROR_DELIVERY_FAILED,
            details="Nie udalo sie przekazac klucza publicznego do drugiego uzytkownika.",
        )
        await writer.send(encode_message(response))

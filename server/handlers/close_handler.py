from typing import Any

import websockets

from ..response_builder import close_notice, error
from common.errors import ERROR_SESSION_INVALID
from ..session_manager import SessionManager
from common.models import CloseRequestFrame
from common.protocol import encode_message


async def handle_close(
    message_json: CloseRequestFrame,
    addr: tuple,
    writer: Any,
    session_manager: SessionManager,
) -> bool:
    close_session_id = message_json.session_id
    participant_writers = await session_manager.close_session_and_get_writers(close_session_id)
    if not participant_writers:
        response = error(
            code=ERROR_SESSION_INVALID,
            details=f"Sesja {close_session_id} nie istnieje lub jest juz zamknieta",
        )
        await writer.send(encode_message(response))
        return False

    notice = close_notice(
        session_id=close_session_id,
        msg_id=message_json.msg_id,
        timestamp=message_json.timestamp,
    )
    encoded_notice = encode_message(notice)

    for participant_writer in participant_writers:
        try:
            await participant_writer.send(encoded_notice)
        except (OSError, websockets.exceptions.ConnectionClosed):
            pass

    print(f"[CLOSE OK] Zamknieto sesje {close_session_id}")
    return True
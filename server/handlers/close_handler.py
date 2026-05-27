import asyncio
from typing import Any

from ..response_builder import close_notice, error
from common.errors import ERROR_SESSION_INVALID
from ..session_manager import SessionManager
from common.models import CloseRequestFrame


async def handle_close(
    message_json: CloseRequestFrame,
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager: SessionManager,
    encode_message: Any,
) -> bool:
    close_session_id = message_json.session_id
    participant_writers = await session_manager.close_session_and_get_writers(close_session_id)
    if not participant_writers:
        response = error(
            code=ERROR_SESSION_INVALID,
            details=f"Sesja {close_session_id} nie istnieje lub jest juz zamknieta",
        )
        writer.write(encode_message(response))
        await writer.drain()
        return False

    notice = close_notice(
        session_id=close_session_id,
        msg_id=message_json.msg_id,
        timestamp=message_json.timestamp,
    )
    encoded_notice = encode_message(notice)

    for participant_writer in participant_writers:
        try:
            participant_writer.write(encoded_notice)
            await participant_writer.drain()
        except OSError:
            pass

    print(f"[CLOSE OK] Zamknieto sesje {close_session_id}")
    return True

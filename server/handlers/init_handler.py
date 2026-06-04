from typing import Any

from server.response_builder import init_ok
from server.session_manager import SessionManager
from common.models import InitFrame
from common.protocol import encode_message


async def handle_init(
    message_json: InitFrame,
    addr: tuple,
    writer: Any,
    session_manager: SessionManager,
) -> str:
    created_session_id, jwt_token = await session_manager.create_session(addr)
    response = init_ok(
        session_id=created_session_id,
        msg_id=message_json.msg_id,
        timestamp=message_json.timestamp,
        token=jwt_token,
    )
    await writer.send(encode_message(response))
    print(f"[INIT OK] Utworzona sesja {created_session_id} dla {addr}")
    return created_session_id

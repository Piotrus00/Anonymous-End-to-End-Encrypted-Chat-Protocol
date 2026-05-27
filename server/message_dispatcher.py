import asyncio
from typing import Dict, Any, Optional

from .handlers.init_handler import handle_init
from .handlers.join_handler import handle_join
from .handlers.msg_handler import handle_msg
from .handlers.close_handler import handle_close
from .handlers.pong_handler import handle_pong
from .handlers.ack_handler import handle_ack
from .response_builder import error
from common.errors import ERROR_UNKNOWN_TYPE

message_handlers = {
    "INIT": handle_init,
    "JOIN": handle_join,
    "MSG": handle_msg,
    "ACK": handle_ack,
    "CLOSE": handle_close,
    "PONG": handle_pong,
}

async def dispatch(
    message_json: Dict[str, Any],
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager,
    encode_message,
) -> Optional[str]:
    message_type = message_json.get("type")
    handler = message_handlers.get(message_type)

    if not handler:
        response = error(
            code=ERROR_UNKNOWN_TYPE,
            details=f"Nieznany typ wiadomosci: {message_type}",
        )
        writer.write(encode_message(response))
        await writer.drain()
        return None

    if message_type in ("INIT", "JOIN"):
        return await handler(message_json, addr, writer, session_manager, encode_message)
    elif message_type in ("MSG", "ACK"):
        await handler(message_json, addr, writer, session_manager, encode_message)
        return None
    elif message_type == "CLOSE":
        if await handler(message_json, writer, session_manager, encode_message):
            return "CLOSE"
        return None
    elif message_type == "PONG":
        await handler()  # Correctly call pong handler without arguments
        return None
    return None

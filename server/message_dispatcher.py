import asyncio
from typing import Any, Optional

from .handlers.init_handler import handle_init
from .handlers.join_handler import handle_join
from .handlers.msg_handler import handle_msg
from .handlers.close_handler import handle_close
from .handlers.pong_handler import handle_pong
from .handlers.ack_handler import handle_ack
from .response_builder import error
from common.errors import ERROR_UNKNOWN_TYPE
from common.models import ProtocolMessage

message_handlers: dict[str, Any] = {
    "INIT": handle_init,
    "JOIN": handle_join,
    "MSG": handle_msg,
    "ACK": handle_ack,
    "CLOSE": handle_close,
    "PONG": handle_pong,
}

async def dispatch(
    message_json: ProtocolMessage,
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager,
    encode_message,
) -> Optional[str]:
    message_type = message_json.type
    handler = message_handlers.get(message_type)

    if not handler:
        response = error(
            code=ERROR_UNKNOWN_TYPE,
            details=f"Nieznany typ wiadomosci: {message_type}",
        )
        writer.write(encode_message(response))
        await writer.drain()
        return None

    result = await handler(message_json, addr, writer, session_manager, encode_message)

    match message_type:
        case "INIT" | "JOIN":
            return result if isinstance(result, str) else None
        case "CLOSE":
            if result:
                return "CLOSE"
            return None
        case _:
            return None

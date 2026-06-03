from typing import Any, Optional

from .handlers.init_handler import handle_init
from .handlers.join_handler import handle_join
from .handlers.msg_handler import handle_msg
from .handlers.close_handler import handle_close
from .handlers.ack_handler import handle_ack
from .handlers.key_exchange_handler import handle_key_exchange
from .response_builder import error
from common.errors import ERROR_UNKNOWN_TYPE
from common.models import ProtocolMessage
from common.protocol import encode_message

message_handlers: dict[str, Any] = {
    "INIT": handle_init,
    "JOIN": handle_join,
    "KEY_EXCHANGE": handle_key_exchange,
    "MSG": handle_msg,
    "ACK": handle_ack,
    "CLOSE": handle_close,
}

async def dispatch(
    message_json: ProtocolMessage,
    addr: tuple,
    writer: Any,
    session_manager,
) -> Optional[str]:
    message_type = message_json.type
    handler = message_handlers.get(message_type)

    if not handler:
        response = error(
            code=ERROR_UNKNOWN_TYPE,
            details=f"Nieznany typ wiadomosci: {message_type}",
        )
        await writer.send(encode_message(response))
        return None

    result = await handler(message_json, addr, writer, session_manager)

    match message_type:
        case "INIT" | "JOIN":
            return result if isinstance(result, str) else None
        case "CLOSE":
            if result:
                return "CLOSE"
            return None
        case _:
            return None
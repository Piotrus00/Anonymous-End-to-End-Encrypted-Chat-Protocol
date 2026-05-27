import asyncio
from typing import Any

async def handle_pong(
    message_json: Any,
    addr: tuple,
    writer: asyncio.StreamWriter,
    session_manager: Any,
) -> None:
    pass
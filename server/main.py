import asyncio
from functools import partial

import websockets

from .client_handler import handle_client
from common.config import HOST, PORT, KEEP_ALIVE_INTERVAL, MAX_MISSED_PINGS, MAX_MESSAGE_SIZE
from .session_manager import SessionManager

session_manager = SessionManager()


async def main():
    """Main entry point for the asyncio server."""
    handler = partial(
        handle_client,
        session_manager=session_manager
    )

    print(f"[START] Serwer nasluchuje na {HOST}:{PORT}")

    async with websockets.serve(
        handler,
        HOST,
        PORT,
        max_size=MAX_MESSAGE_SIZE,
        ping_interval=KEEP_ALIVE_INTERVAL,
        ping_timeout=KEEP_ALIVE_INTERVAL * MAX_MISSED_PINGS,
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Serwer zatrzymywany...")
import asyncio
import time
from functools import partial

import websockets

from common.protocol import encode_message
from .response_builder import ping, error

from .client_handler import handle_client
from common.config import HOST, PORT, KEEP_ALIVE_INTERVAL, MAX_MISSED_PINGS, MAX_MESSAGE_SIZE
from common.errors import ERROR_DISCONNECTED
from .session_manager import SessionManager

session_manager = SessionManager()


async def keep_alive_loop(manager: SessionManager):
    """Periodically pings inactive clients and disconnects timed-out ones."""
    while True:
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)

        clients_snapshot = []
        async with manager.lock:
            clients_snapshot = list(manager.client_status.items())

        for client_addr, status in clients_snapshot:
            if status["missed_pings_count"] >= MAX_MISSED_PINGS:
                print(f"[TIMEOUT] Klient {client_addr} przekroczyl limit odpowiedzi. Rozlaczanie.")
                
                session_id = await manager.find_session_by_addr(client_addr)
                if session_id:
                    peer_writer = await manager.get_peer_writer(session_id, client_addr)
                    if peer_writer:
                        try:
                            error_message = error(
                                code=ERROR_DISCONNECTED,
                                details="Drugi uczestnik utracil polaczenie z powodu braku aktywonsci.",
                            )
                            await peer_writer.send(encode_message(error_message))
                        except (ConnectionError, OSError, websockets.exceptions.ConnectionClosed):
                            pass
                
                await manager.disconnect_client(client_addr)
                continue

            if time.monotonic() - status["last_activity_time"] > KEEP_ALIVE_INTERVAL:
                writer_to_ping = None
                async with manager.lock:
                    if client_addr in manager.writers:
                        writer_to_ping = manager.writers[client_addr]

                if writer_to_ping:
                    try:
                        ping_message = ping(msg_id="ping_123", timestamp=int(time.time()))
                        await writer_to_ping.send(encode_message(ping_message))
                        await manager.increment_missed_pings(client_addr)
                        print(f"[PING] Wyslano PING do {client_addr}")
                    except (ConnectionError, OSError, websockets.exceptions.ConnectionClosed):
                        # Klient rozłączył się w międzyczasie, pętla główna to obsłuży
                        pass


async def main():
    """Main entry point for the asyncio server."""
    handler = partial(
        handle_client,
        session_manager=session_manager
    )

    print(f"[START] Serwer nasluchuje na {HOST}:{PORT}")

    asyncio.create_task(keep_alive_loop(session_manager))

    async with websockets.serve(handler, HOST, PORT, max_size=MAX_MESSAGE_SIZE):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Serwer zatrzymywany...")
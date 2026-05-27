import asyncio
import time
from functools import partial

from common.protocol import decode_message, encode_message
from .response_builder import ping, error

from .client_handler import handle_client
from common.config import HOST, PORT, KEEP_ALIVE_INTERVAL, MAX_MISSED_PINGS
from common.errors import ERROR_DISCONNECTED
from .session_manager import SessionManager

session_manager = SessionManager()


async def keep_alive_loop(manager: SessionManager, encode_message_func):
    """Periodically pings inactive clients and disconnects timed-out ones."""
    while True:
        await asyncio.sleep(KEEP_ALIVE_INTERVAL)

        clients_snapshot = []
        async with manager.lock:
            clients_snapshot = list(manager.client_status.items())

        for client_addr, status in clients_snapshot:
            if status["missed_pings_count"] >= MAX_MISSED_PINGS:
                print(f"[TIMEOUT] Klient {client_addr} przekroczyl limit odpowiedzi.")

                writer_to_close = None
                async with manager.lock:
                    writer_to_close = manager.writers.get(client_addr)

                if writer_to_close:
                    writer_to_close.close()
                    try:
                        await writer_to_close.wait_closed()
                    except (ConnectionError, OSError):
                        pass

                await manager.unregister_connection(client_addr)

                session_to_notify = None
                async with manager.lock:
                    for session_id, participants in manager.sessions.items():
                        if client_addr in participants:
                            session_to_notify = session_id
                            break

                if session_to_notify:
                    peer_writer = await manager.get_peer_writer(session_to_notify, client_addr)
                    if peer_writer:
                        try:
                            error_message = error(
                                code=ERROR_DISCONNECTED,
                                details="Drugi uczestnik utracil polaczenie",
                            )
                            peer_writer.write(encode_message_func(error_message))
                            await peer_writer.drain()
                        except (ConnectionError, OSError):
                            pass

                    await manager.remove_from_session(client_addr, session_to_notify)
                continue

            if time.time() - status["last_activity_time"] > KEEP_ALIVE_INTERVAL:
                writer_to_ping = None
                async with manager.lock:
                    if client_addr in manager.writers:
                        writer_to_ping = manager.writers[client_addr]

                if writer_to_ping:
                    try:
                        ping_message = ping(msg_id="ping_123", timestamp=int(time.time()))
                        writer_to_ping.write(encode_message_func(ping_message))
                        await writer_to_ping.drain()
                        await manager.increment_missed_pings(client_addr)
                        print(f"[PING] Wyslano PING do {client_addr}")
                    except (ConnectionError, OSError):
                        pass


async def main():
    """Main entry point for the asyncio server."""
    handler = partial(
        handle_client,
        session_manager=session_manager,
        decode_message=decode_message,
        encode_message=encode_message,
    )

    server = await asyncio.start_server(handler, HOST, PORT)

    print(f"[START] Serwer nasluchuje na {HOST}:{PORT}")

    asyncio.create_task(keep_alive_loop(session_manager, encode_message))

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] Serwer zatrzymywany...")

import asyncio
import ssl

import websockets

from common.config import (
    HOST,
    PORT,
    KEEP_ALIVE_INTERVAL,
    MAX_MISSED_PINGS,
    MAX_MESSAGE_SIZE,
    TLS_ENABLED,
    websocket_uri,
)
from common.tls import create_client_ssl_context
from .api.init_api import send_init
from .api.join_api import send_join
from .client import ChatClient


async def main():
    ssl_context: ssl.SSLContext | None = None
    if TLS_ENABLED:
        ssl_context = create_client_ssl_context()

    try:
        async with websockets.connect(
            websocket_uri(),
            ssl=ssl_context,
            max_size=MAX_MESSAGE_SIZE,
            ping_interval=KEEP_ALIVE_INTERVAL,
            ping_timeout=KEEP_ALIVE_INTERVAL * MAX_MISSED_PINGS,
        ) as websocket:
            print(f"Polaczono z serwerem ({websocket_uri()})!")
            client = ChatClient(websocket)

            print("\n[1] Tworzyc nowa sesje (INIT)")
            print("[2] Dolaczyc do istniejacej sesji (JOIN)")
            choice = await asyncio.to_thread(input, "\nWybierz opcje (1 lub 2): ")
            choice = choice.strip()

            if choice == "1":
                session_id, auth_token = await send_init(websocket)
                if session_id and auth_token:
                    print(f"\nPrzekaz session_id drugiemu uzytkownikowi: {session_id}")
                    await client.start(session_id, auth_token, is_initiator=True)

            elif choice == "2":
                session_id_input = await asyncio.to_thread(input, "Wpisz session_id sesji, do ktorej chcesz dolaczyc: ")
                session_id_input = session_id_input.strip()
                if not session_id_input:
                    print("X session_id nie moze byc pusty")
                else:
                    joined, auth_token = await send_join(websocket, session_id_input)
                    if joined and auth_token:
                        await client.start(session_id_input, auth_token, is_initiator=False)
            else:
                print("X Niepoprawny wybor")
    except (
        ConnectionRefusedError,
        OSError,
        websockets.exceptions.InvalidURI,
        websockets.exceptions.InvalidHandshake,
        ssl.SSLError,
    ):
        print(f"X Nie mozna polaczyc sie z serwerem {websocket_uri()}")
        return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SYSTEM] Klient zamkniety.")

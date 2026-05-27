import asyncio

from common.protocol import decode_message, encode_message
from common.config import HOST, PORT
from .api.init_api import send_init
from .api.join_api import send_join
from .client import ChatClient


async def main():
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except (ConnectionRefusedError, OSError):
        print(f"X Nie mozna polaczyc sie z serwerem {HOST}:{PORT}")
        return

    print("Polaczono z serwerem!")
    client = ChatClient(reader, writer)

    try:
        print("\n[1] Tworzyc nowa sesje (INIT)")
        print("[2] Dolaczyc do istniejacej sesji (JOIN)")
        choice = await asyncio.to_thread(input, "\nWybierz opcje (1 lub 2): ")
        choice = choice.strip()

        if choice == "1":
            session_id = await send_init(reader, writer, encode_message, decode_message)
            if session_id:
                print(f"\nPrzekaz session_id drugiemu uzytkownikowi: {session_id}")
                await client.start(session_id, is_initiator=True)

        elif choice == "2":
            session_id_input = await asyncio.to_thread(input, "Wpisz session_id sesji, do ktorej chcesz dolaczyc: ")
            session_id_input = session_id_input.strip()
            if not session_id_input:
                print("X session_id nie moze byc pusty")
            elif await send_join(reader, writer, session_id_input, encode_message, decode_message):
                await client.start(session_id_input, is_initiator=False)
        else:
            print("X Niepoprawny wybor")

    finally:
        print("\n[SYSTEM] Zamykanie polaczenia...")
        if writer:
            writer.close()
            await writer.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SYSTEM] Klient zamkniety.")
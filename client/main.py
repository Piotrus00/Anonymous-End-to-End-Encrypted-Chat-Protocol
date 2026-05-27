import asyncio
import time
from typing import Dict, List

from common.protocol import decode_message, encode_message
from common.config import HOST, PORT, ACK_TIMEOUT, MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from .api.init_api import send_init
from .api.join_api import send_join
from .api.message_api import build_msg_frame
from .api.close_api import send_close
from .receiver import receiver_loop

unacked_messages: Dict[str, float] = {}
unacked_lock = asyncio.Lock()


async def check_ack_timeouts(stop_event: asyncio.Event):
    while not stop_event.is_set():
        await asyncio.sleep(1)
        async with unacked_lock:
            for msg_id, sent_time in list(unacked_messages.items()):
                if time.time() - sent_time > ACK_TIMEOUT:
                    print(f"\n[SYSTEM] Nie otrzymano potwierdzenia dla wiadomosci {msg_id}")
                    unacked_messages.pop(msg_id, None)


async def user_input_loop(
    writer: asyncio.StreamWriter,
    session_id: str,
    stop_event: asyncio.Event,
):
    local_message_timestamps: List[float] = []
    while not stop_event.is_set():
        try:
            text = await asyncio.to_thread(input, "Ty: ")
            text = text.strip()

            if text.lower() == "exit":
                await send_close(writer, session_id, encode_message)
                stop_event.set()
                break
            if not text:
                continue

            current_time = time.time()
            local_message_timestamps = [ts for ts in local_message_timestamps if current_time - ts <= RATE_LIMIT_WINDOW]

            if len(local_message_timestamps) >= RATE_LIMIT_MESSAGES:
                print("X Przekroczono limit wiadomosci. Sprobuj ponownie za chwile.")
                continue

            msg_id, frame = build_msg_frame(session_id, text)
            encoded_frame = encode_message(frame)

            if len(encoded_frame) > MAX_MESSAGE_SIZE:
                print(f"X Wiadomosc jest zbyt dluga ({len(encoded_frame)}/{MAX_MESSAGE_SIZE} bajtow) i nie zostala wyslana.")
                continue

            local_message_timestamps.append(current_time)

            async with unacked_lock:
                unacked_messages[msg_id] = current_time

            writer.write(encoded_frame)
            await writer.drain()
            print(f"[SYSTEM] Wyslano wiadomosc {msg_id}, oczekiwanie na ACK...")
        except (EOFError, KeyboardInterrupt):
            stop_event.set()
            break


async def chat_loop(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    session_id: str,
):
    print("\nMozesz wysylac MSG. Wpisz 'exit' aby wyslac CLOSE i zakonczyc.")
    stop_event = asyncio.Event()

    receiver_task = asyncio.create_task(
        receiver_loop(reader, writer, encode_message, decode_message, unacked_messages, unacked_lock, stop_event)
    )
    timeout_task = asyncio.create_task(check_ack_timeouts(stop_event))
    input_task = asyncio.create_task(user_input_loop(writer, session_id, stop_event))

    await asyncio.gather(receiver_task, timeout_task, input_task, return_exceptions=True)


async def main():
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
    except (ConnectionRefusedError, OSError):
        print(f"X Nie mozna polaczyc sie z serwerem {HOST}:{PORT}")
        return

    print("Polaczono z serwerem!")

    try:
        print("\n[1] Tworzyc nowa sesje (INIT)")
        print("[2] Dolaczyc do istniejacej sesji (JOIN)")
        choice = await asyncio.to_thread(input, "\nWybierz opcje (1 lub 2): ")
        choice = choice.strip()

        session_id = None
        if choice == "1":
            session_id = await send_init(reader, writer, encode_message, decode_message)
            if session_id:
                print(f"\nPrzekaz session_id drugiemu uzytkownikowi: {session_id}")
                await chat_loop(reader, writer, session_id)

        elif choice == "2":
            session_id_input = await asyncio.to_thread(input, "Wpisz session_id sesji, do ktorej chcesz dolaczyc: ")
            session_id_input = session_id_input.strip()
            if not session_id_input:
                print("X session_id nie moze byc pusty")
            elif await send_join(reader, writer, session_id_input, encode_message, decode_message):
                await chat_loop(reader, writer, session_id_input)
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

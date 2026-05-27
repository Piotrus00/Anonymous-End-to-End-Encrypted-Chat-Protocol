import asyncio
from typing import Dict

from .api.pong_api import build_pong_frame
from .api.ack_api import build_ack_frame


async def receiver_loop(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    encode_message,
    decode_message,
    unacked_messages: Dict[str, float],
    unacked_lock: asyncio.Lock,
    stop_event: asyncio.Event,
    chat_ready_event: asyncio.Event,
):
    while not stop_event.is_set():
        try:
            message_bytes = await reader.readuntil(b'\n')
            if not message_bytes:
                break

            success, response = decode_message(message_bytes.strip())
            if not success:
                continue

            if response is None:
                continue

            response_type = response.type
            if response_type == "MSG":
                text = response.payload.ciphertext
                print(f"\n[MSG] {text}")

                # Send ACK
                ack_frame = build_ack_frame(response.session_id, response.msg_id)
                writer.write(encode_message(ack_frame))
                await writer.drain()

            elif response_type == "ACK":
                acked_msg_id = response.payload.acked_msg_id
                async with unacked_lock:
                    if acked_msg_id in unacked_messages:
                        unacked_messages.pop(acked_msg_id, None)
                        print(f"\n[SYSTEM] Otrzymano potwierdzenie dla {acked_msg_id}")

            elif response_type == "JOIN_OK":
                print("\n[SYSTEM] Drugi uzytkownik dolaczyl do sesji. Mozna rozmawiac.")
                chat_ready_event.set()

            elif response_type == "CLOSE":
                closed_sid = response.session_id
                print(f"\n[CLOSE] Sesja {closed_sid} zostala zamknieta")
                stop_event.set()
                break
            elif response_type == "PING":
                pong_frame = build_pong_frame()
                writer.write(encode_message(pong_frame))
                await writer.drain()
            elif response_type == "ERROR":
                print(f"\n[ERROR] {response.details}")

        except (asyncio.IncompleteReadError, ConnectionError, OSError):
            print("\n[SYSTEM] Utracono polaczenie z serwerem.")
            stop_event.set()
            break
    print("[SYSTEM] Petla odbiornika zakonczona.")

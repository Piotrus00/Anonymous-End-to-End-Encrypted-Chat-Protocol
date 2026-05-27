import asyncio
import time
from typing import Dict, List, Optional

from common.protocol import decode_message, encode_message
from common.config import ACK_TIMEOUT, MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from .api.close_api import send_close
from .api.message_api import build_msg_frame
from .api.pong_api import build_pong_frame
from .api.ack_api import build_ack_frame


class ChatClient:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.unacked_messages: Dict[str, float] = {}
        self.unacked_lock = asyncio.Lock()
        self.stop_event = asyncio.Event()
        self.chat_ready_event = asyncio.Event()
        self.session_id: Optional[str] = None

    async def start(self, session_id: str, is_initiator: bool):
        self.session_id = session_id
        if not is_initiator:
            self.chat_ready_event.set()
        else:
            print("\n[SYSTEM] Oczekiwanie na dolaczenie drugiego uzytkownika...")

        receiver_task = asyncio.create_task(self.receiver_loop())
        timeout_task = asyncio.create_task(self.check_ack_timeouts())
        input_task = asyncio.create_task(self.user_input_loop())

        await asyncio.gather(receiver_task, timeout_task, input_task, return_exceptions=True)

    async def check_ack_timeouts(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(1)
            async with self.unacked_lock:
                for msg_id, sent_time in list(self.unacked_messages.items()):
                    if time.monotonic() - sent_time > ACK_TIMEOUT:
                        print(f"\n[SYSTEM] Nie otrzymano potwierdzenia dla wiadomosci {msg_id}")
                        self.unacked_messages.pop(msg_id, None)

    async def user_input_loop(self):
        await self.chat_ready_event.wait()
        print("\nMozesz wysylac MSG. Wpisz 'exit' aby wyslac CLOSE i zakonczyc.")

        local_message_timestamps: List[float] = []
        while not self.stop_event.is_set():
            try:
                text = await asyncio.to_thread(input, "Ty: ")
                text = text.strip()

                if text.lower() == "exit":
                    await send_close(self.writer, self.session_id, encode_message)
                    self.stop_event.set()
                    break
                if not text:
                    continue

                current_time = time.monotonic()
                local_message_timestamps = [ts for ts in local_message_timestamps if current_time - ts <= RATE_LIMIT_WINDOW]

                if len(local_message_timestamps) >= RATE_LIMIT_MESSAGES:
                    print("X Przekroczono limit wiadomosci. Sprobuj ponownie za chwile.")
                    continue

                msg_id, frame = build_msg_frame(self.session_id, text)
                encoded_frame = encode_message(frame)

                if len(encoded_frame) > MAX_MESSAGE_SIZE:
                    print(f"X Wiadomosc jest zbyt dluga ({len(encoded_frame)}/{MAX_MESSAGE_SIZE} bajtow) i nie zostala wyslana.")
                    continue

                local_message_timestamps.append(current_time)

                async with self.unacked_lock:
                    self.unacked_messages[msg_id] = current_time

                self.writer.write(encoded_frame)
                await self.writer.drain()
                print(f"[SYSTEM] Wyslano wiadomosc {msg_id}, oczekiwanie na ACK...")
            except (EOFError, KeyboardInterrupt):
                self.stop_event.set()
                break

    async def receiver_loop(self):
        while not self.stop_event.is_set():
            try:
                message_bytes = await self.reader.readuntil(b'\n')
                if not message_bytes:
                    break

                success, response = decode_message(message_bytes.strip())
                if not success or response is None:
                    continue

                response_type = response.type
                if response_type == "MSG":
                    text = response.payload.ciphertext
                    print(f"\n[MSG] {text}")

                    ack_frame = build_ack_frame(response.session_id, response.msg_id)
                    self.writer.write(encode_message(ack_frame))
                    await self.writer.drain()

                elif response_type == "ACK":
                    acked_msg_id = response.payload.acked_msg_id
                    async with self.unacked_lock:
                        if acked_msg_id in self.unacked_messages:
                            self.unacked_messages.pop(acked_msg_id, None)
                            print(f"\n[SYSTEM] Otrzymano potwierdzenie dla {acked_msg_id}")

                elif response_type == "JOIN_OK":
                    print("\n[SYSTEM] Drugi uzytkownik dolaczyl do sesji. Mozna rozmawiac.")
                    self.chat_ready_event.set()

                elif response_type == "CLOSE":
                    closed_sid = response.session_id
                    print(f"\n[CLOSE] Sesja {closed_sid} zostala zamknieta")
                    self.stop_event.set()
                    break
                elif response_type == "PING":
                    pong_frame = build_pong_frame()
                    self.writer.write(encode_message(pong_frame))
                    await self.writer.drain()
                elif response_type == "ERROR":
                    print(f"\n[ERROR] {response.details}")

            except (asyncio.IncompleteReadError, ConnectionError, OSError):
                print("\n[SYSTEM] Utracono polaczenie z serwerem.")
                self.stop_event.set()
                break
        print("[SYSTEM] Petla odbiornika zakonczona.")
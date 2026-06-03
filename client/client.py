import asyncio
import time
from typing import Any, Dict, Optional

import websockets

from common.protocol import decode_message, encode_message
from common.config import ACK_TIMEOUT, MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from .api.close_api import send_close
from .api.message_api import build_msg_frame
from .api.pong_api import build_pong_frame
from .api.ack_api import build_ack_frame


class ChatClient:
    def __init__(self, websocket: Any):
        self.websocket = websocket
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

        # Token Bucket algorithm variables - inicjalizuj bucket na pełną pojemność
        local_tokens_available: float = float(RATE_LIMIT_MESSAGES)
        local_last_refill_time: float = time.monotonic()

        while not self.stop_event.is_set():
            try:
                text = await asyncio.to_thread(input, "Ty: ")
                text = text.strip()

                if text.lower() == "exit":
                    await send_close(self.websocket, self.session_id)
                    self.stop_event.set()
                    break
                if not text:
                    continue

                current_time = time.monotonic()

                # Token Bucket refill logic
                refill_rate = RATE_LIMIT_MESSAGES / RATE_LIMIT_WINDOW
                time_elapsed = current_time - local_last_refill_time
                tokens_to_add = time_elapsed * refill_rate
                local_tokens_available = min(
                    RATE_LIMIT_MESSAGES,  # Max capacity
                    local_tokens_available + tokens_to_add
                )
                local_last_refill_time = current_time

                # Check if we can send a message (need 1 token)
                if local_tokens_available < 1.0:
                    print("X Przekroczono limit wiadomosci. Sprobuj ponownie za chwile.")
                    continue

                msg_id, frame = build_msg_frame(self.session_id, text)
                encoded_frame = encode_message(frame)

                if len(encoded_frame) > MAX_MESSAGE_SIZE:
                    print(f"X Wiadomosc jest zbyt dluga ({len(encoded_frame)}/{MAX_MESSAGE_SIZE} bajtow) i nie zostala wyslana.")
                    continue

                local_tokens_available -= 1.0

                async with self.unacked_lock:
                    self.unacked_messages[msg_id] = current_time

                await self.websocket.send(encoded_frame)
                print(f"[SYSTEM] Wyslano wiadomosc {msg_id}, oczekiwanie na ACK...")
            except (EOFError, KeyboardInterrupt):
                self.stop_event.set()
                break

    async def receiver_loop(self):
        while not self.stop_event.is_set():
            try:
                message = await self.websocket.recv()
                if not message:
                    break

                if isinstance(message, str):
                    message_bytes = message.encode("utf-8")
                else:
                    message_bytes = message

                success, response = decode_message(message_bytes.strip())
                if not success or response is None:
                    continue

                response_type = response.type
                if response_type == "MSG":
                    text = response.payload.ciphertext
                    print(f"\n[MSG] {text}")

                    ack_frame = build_ack_frame(response.session_id, response.msg_id)
                    await self.websocket.send(encode_message(ack_frame))

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
                    await self.websocket.send(encode_message(pong_frame))
                elif response_type == "ERROR":
                    print(f"\n[ERROR] {response.details}")
            except websockets.exceptions.PayloadTooBig:
                print(f"\n[SYSTEM] Odrzucono odpowiedz serwera: przekroczono limit {MAX_MESSAGE_SIZE} bajtow")
                self.stop_event.set()
                break
            except (websockets.exceptions.ConnectionClosed, ConnectionError, OSError):
                print("\n[SYSTEM] Utracono polaczenie z serwerem.")
                self.stop_event.set()
                break
        print("[SYSTEM] Petla odbiornika zakonczona.")
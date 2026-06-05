import asyncio
import time
import shutil
from typing import Any, Dict, Optional

import websockets

from common.crypto import CryptoSession
from common.protocol import decode_message, encode_message
from common.config import ACK_TIMEOUT, MAX_MESSAGE_SIZE, RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW
from .api.close_api import send_close
from .api.message_api import build_msg_frame
from .api.ack_api import build_ack_frame
from .api.key_exchange_api import send_key_exchange
from .auth_store import ClientAuthStore


class ChatClient:

    UP = "\x1b[A"       # karetka na linie wyżej
    CLEAR = "\x1b[K"    # czyszczenie lini

    def __init__(self, websocket: Any):
        self.websocket = websocket
        self.auth = ClientAuthStore()
        self.crypto = CryptoSession()
        self.unacked_messages: Dict[str, float] = {}
        self.unacked_lock = asyncio.Lock()
        self.stop_event = asyncio.Event()
        self.chat_ready_event = asyncio.Event()
        self.session_id: Optional[str] = None
        self._key_exchange_sent = False
        self.terminal_width = shutil.get_terminal_size().columns // 2

    async def start(self, session_id: str, auth_token: str, is_initiator: bool):
        self.session_id = session_id
        self.auth.set(session_id, auth_token)
        if is_initiator:
            print("\n[SYSTEM] Oczekiwanie na dolaczenie drugiego uzytkownika...")
        else:
            print("\n[SYSTEM] Rozpoczynam wymiane kluczy...")
            await self._send_key_exchange()

        # Uruchom wszystkie trzy zadania:
        receiver_task = asyncio.create_task(self.receiver_loop()) # Odbieranie wiadomości od serwera
        timeout_task = asyncio.create_task(self.check_ack_timeouts()) # Sprawdzanie, czy nie minął czas oczekiwania na ACK dla wysłanych wiadomości
        input_task = asyncio.create_task(self.user_input_loop()) # Obsługa wejścia użytkownika - wysyłanie wiadomości i komendy exit

        await asyncio.gather(receiver_task, timeout_task, input_task, return_exceptions=True) # Czekaj na zakończenie wszystkich zadań

    async def _maybe_enable_chat(self) -> None:
        if self._key_exchange_sent and self.crypto.is_ready:
            self.chat_ready_event.set()
            print("\n[SYSTEM] Wymiana kluczy zakonczona. Mozna rozmawiac (E2EE).")

    async def _send_key_exchange(self) -> None:
        if self._key_exchange_sent or self.session_id is None:
            return
        await send_key_exchange(
            self.websocket,
            self.session_id,
            self.auth.require_token(),
            self.crypto.public_key_b64(),
        )
        self._key_exchange_sent = True
        print("[SYSTEM] Wyslano klucz publiczny (KEY_EXCHANGE)")
        await self._maybe_enable_chat()

    async def _on_key_exchange_received(self, public_key_b64: str) -> None:
        try:
            self.crypto.set_peer_public_key(public_key_b64)
        except (ValueError, RuntimeError) as exc:
            print(f"\n[ERROR] Nie udalo sie przetworzyc klucza publicznego peer-a: {exc}")
            return

        await self._maybe_enable_chat()


    #  kazda wyslana wiadomosc jest zapisywana w unacked_messages z timestampem wyslania.
    #  Ten task co sekundę sprawdza, czy dla którejś z nich nie minął czas oczekiwania na ACK (10sekund).
    #  Jeśli tak, usuwa ją z unacked_messages i informuje użytkownika, że nie otrzymał potwierdzenia.
    async def check_ack_timeouts(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(1)
            async with self.unacked_lock:
                for msg_id, sent_time in list(self.unacked_messages.items()):
                    if time.monotonic() - sent_time > ACK_TIMEOUT:
                        print(f"\n[SYSTEM] Nie otrzymano potwierdzenia dla wiadomosci {msg_id}")
                        self.unacked_messages.pop(msg_id, None)

    async def user_input_loop(self):
        await self.chat_ready_event.wait() # czekamy na drugiego użytkownika, zanim pozwolimy na wysyłanie wiadomości
        print("\nMozesz wysylac MSG. Wpisz 'exit' aby zakonczyc.")

        # Token Bucket algorithm variables - inicjalizuj bucket na pełną pojemność
        local_tokens_available: float = float(RATE_LIMIT_MESSAGES)
        local_last_refill_time: float = time.monotonic()

        while not self.stop_event.is_set():
            try:
                text = await asyncio.to_thread(input)
                text = text.strip()

                if text.lower() == "exit":
                    await send_close(self.websocket, self.session_id, self.auth.require_token())
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
                    RATE_LIMIT_MESSAGES,
                    local_tokens_available + tokens_to_add,
                )
                local_last_refill_time = current_time

                # Check if we can send a message (need 1 token)
                if local_tokens_available < 1.0:
                    print("X Przekroczono limit wiadomosci. Sprobuj ponownie za chwile.")
                    continue

                try:
                    ciphertext = self.crypto.encrypt(text)
                except RuntimeError as exc:
                    print(f"X {exc}")
                    continue

                msg_id, frame = build_msg_frame(
                    self.session_id,
                    self.auth.require_token(),
                    ciphertext,
                ) # Zbuduj ramkę wiadomości, która zawiera session_id, msg_id, token JWT i zaszyfrowany tekst
                encoded_frame = encode_message(frame) # Zakoduj ramkę

                if len(encoded_frame) > MAX_MESSAGE_SIZE:
                    print(f"X Wiadomosc jest zbyt dluga ({len(encoded_frame)}/{MAX_MESSAGE_SIZE} bajtow) i nie zostala wyslana.")
                    continue

                local_tokens_available -= 1.0

                # Dodaj wiadomość do unacked_messages z aktualnym timestampem
                async with self.unacked_lock:
                    self.unacked_messages[msg_id] = current_time

                await self.websocket.send(encoded_frame) # Wyślij zakodowaną ramkę do serwera
                # print(f"[SYSTEM] Wyslano wiadomosc {msg_id}, oczekiwanie na ACK...")
            except (EOFError, KeyboardInterrupt):
                self.stop_event.set()
                break

            print(f'{self.UP}{self.CLEAR}{text:>{self.terminal_width}}', end='')

    async def receiver_loop(self):
        while not self.stop_event.is_set(): # Pętla odbierająca wiadomości od serwera, działa dopóki nie zostanie ustawiony stop_event
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

                response_type = response.type # Sprawdź typ odpowiedzi i obsłuż odpowiednio:
                if response_type == "MSG":
                    try:
                        text = self.crypto.decrypt(response.payload.ciphertext)
                    except (RuntimeError, ValueError) as exc:
                        print(f"\n[ERROR] Nie udalo sie odszyfrowac wiadomosci: {exc}")
                        continue

                    print(f"R> {text}")

                    ack_frame = build_ack_frame(
                        response.session_id,
                        self.auth.require_token(),
                        response.msg_id,
                    )
                    await self.websocket.send(encode_message(ack_frame)) # Po otrzymaniu wiadomości, zbuduj ramkę ACK i wyślij ją do serwera, aby potwierdzić odbiór

                elif response_type == "ACK":
                    acked_msg_id = response.payload.acked_msg_id
                    async with self.unacked_lock:
                        if acked_msg_id in self.unacked_messages:
                            self.unacked_messages.pop(acked_msg_id, None)
                            print(f" -> Dostarczono")

                elif response_type == "KEY_EXCHANGE":
                    await self._on_key_exchange_received(response.payload.public_key)

                elif response_type == "JOIN_OK":
                    print("\n[SYSTEM] Drugi uzytkownik dolaczyl do sesji.")
                    await self._send_key_exchange()

                elif response_type == "CLOSE_NOTICE":
                    closed_sid = response.session_id
                    print(f"\n[CLOSE] Sesja {closed_sid} zostala zamknieta")
                    self.stop_event.set()
                    break
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

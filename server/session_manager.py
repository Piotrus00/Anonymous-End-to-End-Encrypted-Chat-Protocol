"""
Zarządzanie sesjami
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from common.config import RATE_LIMIT_MESSAGES
from common.jwt_auth import issue_session_token, new_participant_credential


class SessionManager:
    """Zarządzanie sesjami: session_id -> lista adresów klientów."""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.writers: Dict[tuple, Any] = {}
        self.client_status: Dict[tuple, Dict] = {}
        # addr -> {session_id, pc} — anonimowe powiązanie połączenia z JWT (bez danych użytkownika)
        self.credentials: Dict[tuple, Dict[str, str]] = {}
        self.lock = asyncio.Lock()

    async def register_connection(self, client_addr, writer: Any) -> None:
        async with self.lock:
            self.writers[client_addr] = writer
            self.client_status[client_addr] = {
                "last_activity_time": time.monotonic(),
                "tokens_available": float(RATE_LIMIT_MESSAGES),  # Token Bucket - pełne wiaderko
                "last_refill_time": time.monotonic(),  # Token Bucket algorithm
            }

    async def disconnect_client(self, client_addr: tuple) -> None:
        """Kompleksowo obsługuje rozłączenie klienta."""
        async with self.lock:
            # Zamknij i usuń writer
            writer = self.writers.pop(client_addr, None)
            if writer:
                try:
                    await writer.close()
                    await writer.wait_closed()
                except (ConnectionError, OSError):
                    pass  # Ignoruj błędy, jeśli połączenie już jest zerwane

            # Usuń status klienta
            self.client_status.pop(client_addr, None)
            self.credentials.pop(client_addr, None)

            # Znajdź i usuń klienta z sesji
            session_to_remove_from = None
            for session_id, participants in self.sessions.items():
                if client_addr in participants:
                    participants.remove(client_addr)
                    if not participants:
                        session_to_remove_from = session_id
                    break
            
            # Jeśli sesja jest pusta, usuń ją
            if session_to_remove_from:
                self.sessions.pop(session_to_remove_from, None)

    async def update_client_activity(self, client_addr) -> None:
        async with self.lock:
            if client_addr in self.client_status:
                self.client_status[client_addr]["last_activity_time"] = time.monotonic()

    async def check_and_update_rate_limit(self, client_addr: tuple, limit: int, window: int) -> bool:
        """
        Token Bucket algorithm: Sprawdza, czy klient nie przekracza limitu wiadomości.
        Zwraca False, jeśli limit został przekroczony.
        
        Parametry:
        - limit: pojemność bucketa (maksymalna liczba tokenów)
        - window: okres czasu w sekundach dla refill_rate
        """
        async with self.lock:
            if client_addr not in self.client_status:
                return False

            current_time = time.monotonic()
            status = self.client_status[client_addr]
            
            # Refill rate: tokeny na sekundę
            refill_rate = limit / window
            
            # Czas od ostatniego uzupełnienia
            time_elapsed = current_time - status["last_refill_time"]
            
            # Uzupełnij tokeny
            tokens_to_add = time_elapsed * refill_rate
            status["tokens_available"] = min(
                limit,  # Maks. pojemność bucketa
                status["tokens_available"] + tokens_to_add
            )
            status["last_refill_time"] = current_time
            
            # Sprawdź, czy można pobrać token
            if status["tokens_available"] >= 1.0:
                status["tokens_available"] -= 1.0
                return True
            else:
                return False

    async def create_session(self, client_addr) -> tuple[str, str]:
        """Tworzy sesję, rejestruje uczestnika i zwraca (session_id, jwt_token)."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        participant_credential = new_participant_credential()
        token = issue_session_token(session_id, participant_credential)
        async with self.lock:
            self.sessions[session_id] = [client_addr]
            self.credentials[client_addr] = {
                "session_id": session_id,
                "pc": participant_credential,
            }
        return session_id, token

    async def authorize_participant(
        self,
        client_addr: tuple,
        session_id: str,
        participant_credential: str,
    ) -> Tuple[bool, str]:
        async with self.lock:
            cred = self.credentials.get(client_addr)
            if cred is None:
                return False, "Brak zarejestrowanego uczestnika dla polaczenia"

            if cred["session_id"] != session_id:
                return False, "Polaczenie nie nalezy do tej sesji"

            if cred["pc"] != participant_credential:
                return False, "Token nie pasuje do uczestnika sesji"

            participants = self.sessions.get(session_id)
            if not participants or client_addr not in participants:
                return False, "Sesja nie istnieje lub uczestnik nie jest aktywny"

        return True, ""

    async def get_session(self, session_id: str) -> Optional[List]:
        async with self.lock:
            return self.sessions.get(session_id)

    async def session_exists(self, session_id: str) -> bool:
        async with self.lock:
            return session_id in self.sessions

    async def join_session(self, session_id: str, client_addr) -> Tuple[bool, str, str | None]:
        """Zwraca (sukces, komunikat, jwt_token lub None przy błędzie)."""
        participant_credential = new_participant_credential()
        token = issue_session_token(session_id, participant_credential)
        async with self.lock:
            if session_id not in self.sessions:
                return False, f"Sesja {session_id} nie istnieje", None

            if client_addr in self.sessions[session_id]:
                return False, "Już jesteś w tej sesji", None

            if len(self.sessions[session_id]) >= 2:
                return False, "Sesja jest pełna", None

            self.sessions[session_id].append(client_addr)
            self.credentials[client_addr] = {
                "session_id": session_id,
                "pc": participant_credential,
            }
            return True, f"Dołączono do sesji {session_id}", token

    async def find_session_by_addr(self, client_addr: tuple) -> Optional[str]:
        """Znajduje session_id na podstawie adresu klienta."""
        async with self.lock:
            for session_id, participants in self.sessions.items():
                if client_addr in participants:
                    return session_id
        return None

    async def get_peer_writer(self, session_id: str, sender_addr) -> Optional[Any]:
        """Zwraca writer drugiego uczestnika sesji albo None."""
        async with self.lock:
            participants = self.sessions.get(session_id)
            if not participants:
                return None

            for participant_addr in participants:
                if participant_addr != sender_addr:
                    return self.writers.get(participant_addr)

            return None

    async def close_session_and_get_writers(self, session_id: str) -> Optional[List[Any]]:
        """Zamyka sesje i zwraca listę aktywnych połączeń uczestników."""
        async with self.lock:
            participants = self.sessions.pop(session_id, None)
            if not participants:
                return None

            for participant_addr in participants:
                self.credentials.pop(participant_addr, None)

            participant_writers = [
                self.writers.get(participant_addr)
                for participant_addr in participants
                if participant_addr in self.writers
            ]
            return participant_writers

"""
Zarządzanie sesjami
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Tuple


class SessionManager:
    """Zarządzanie sesjami: session_id -> lista adresów klientów."""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.writers: Dict[tuple, asyncio.StreamWriter] = {}
        self.client_status: Dict[tuple, Dict] = {}
        self.lock = asyncio.Lock()

    async def register_connection(self, client_addr, writer: asyncio.StreamWriter) -> None:
        async with self.lock:
            self.writers[client_addr] = writer
            self.client_status[client_addr] = {
                "last_activity_time": time.monotonic(),
                "missed_pings_count": 0,
                "message_timestamps": [],
            }

    async def unregister_connection(self, client_addr) -> None:
        async with self.lock:
            self.writers.pop(client_addr, None)
            self.client_status.pop(client_addr, None)

    async def update_client_activity(self, client_addr) -> None:
        async with self.lock:
            if client_addr in self.client_status:
                self.client_status[client_addr]["last_activity_time"] = time.monotonic()
                self.client_status[client_addr]["missed_pings_count"] = 0

    async def check_and_update_rate_limit(self, client_addr: tuple, limit: int, window: int) -> bool:
        """Sprawdza, czy klient nie przekracza limitu wiadomości. Zwraca False, jeśli limit został przekroczony."""
        async with self.lock:
            if client_addr not in self.client_status:
                return False

            current_time = time.monotonic()
            timestamps = self.client_status[client_addr]["message_timestamps"]

            # Usuń stare timestampy
            timestamps = [ts for ts in timestamps if current_time - ts <= window]

            if len(timestamps) < limit:
                timestamps.append(current_time)
                self.client_status[client_addr]["message_timestamps"] = timestamps
                return True
            else:
                self.client_status[client_addr]["message_timestamps"] = timestamps
                return False

    async def increment_missed_pings(self, client_addr) -> None:
        async with self.lock:
            if client_addr in self.client_status:
                self.client_status[client_addr]["missed_pings_count"] += 1

    async def get_inactive_clients(self, max_missed_pings: int) -> List[tuple]:
        async with self.lock:
            inactive_clients = []
            for client_addr, status in self.client_status.items():
                if status["missed_pings_count"] >= max_missed_pings:
                    inactive_clients.append(client_addr)
            return inactive_clients

    async def create_session(self, client_addr) -> str:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        async with self.lock:
            self.sessions[session_id] = [client_addr]
        return session_id

    async def get_session(self, session_id: str) -> Optional[List]:
        async with self.lock:
            return self.sessions.get(session_id)

    async def session_exists(self, session_id: str) -> bool:
        async with self.lock:
            return session_id in self.sessions

    async def join_session(self, session_id: str, client_addr) -> Tuple[bool, str]:
        async with self.lock:
            if session_id not in self.sessions:
                return False, f"Sesja {session_id} nie istnieje"

            if client_addr in self.sessions[session_id]:
                return False, "Już jesteś w tej sesji"

            if len(self.sessions[session_id]) >= 2:
                return False, "Sesja jest pełna"

            self.sessions[session_id].append(client_addr)
            return True, f"Dołączono do sesji {session_id}"

    async def remove_from_session(self, client_addr, session_id: str) -> bool:
        """Usuwa klienta z sesji i usuwa sesję, jeśli nie ma już uczestników."""
        async with self.lock:
            participants = self.sessions.get(session_id)
            if not participants or client_addr not in participants:
                return False

            participants.remove(client_addr)
            if not participants:
                self.sessions.pop(session_id, None)

            return True

    async def get_peer_writer(self, session_id: str, sender_addr) -> Optional[asyncio.StreamWriter]:
        """Zwraca writer drugiego uczestnika sesji albo None."""
        async with self.lock:
            participants = self.sessions.get(session_id)
            if not participants:
                return None

            for participant_addr in participants:
                if participant_addr != sender_addr:
                    return self.writers.get(participant_addr)

            return None

    async def close_session_and_get_writers(self, session_id: str) -> List[asyncio.StreamWriter]:
        """Unieważnia sesje i zwraca aktywne writery uczestnikow tej sesji."""
        async with self.lock:
            participants = self.sessions.pop(session_id, None)
            if not participants:
                return []

            result = []
            for participant_addr in participants:
                writer = self.writers.get(participant_addr)
                if writer is not None:
                    result.append(writer)
            return result
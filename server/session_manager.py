"""
Zarządzanie sesjami
"""

import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple


class SessionManager:
    """Zarządzanie sesjami: session_id -> lista adresów klientów."""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.connections: Dict[tuple, object] = {}
        self.client_status: Dict[tuple, Dict] = {}
        self.lock = threading.RLock()

    def register_connection(self, client_addr, conn) -> None:
        with self.lock:
            self.connections[client_addr] = conn
            self.client_status[client_addr] = {
                "last_activity_time": time.time(),
                "missed_pings_count": 0,
                "message_timestamps": [],
            }

    def unregister_connection(self, client_addr) -> None:
        with self.lock:
            self.connections.pop(client_addr, None)
            self.client_status.pop(client_addr, None)

    def update_client_activity(self, client_addr) -> None:
        with self.lock:
            if client_addr in self.client_status:
                self.client_status[client_addr]["last_activity_time"] = time.time()
                self.client_status[client_addr]["missed_pings_count"] = 0

    def check_and_update_rate_limit(self, client_addr: tuple, limit: int, window: int) -> bool:
        """Sprawdza, czy klient nie przekracza limitu wiadomości. Zwraca False, jeśli limit został przekroczony."""
        with self.lock:
            if client_addr not in self.client_status:
                return False

            current_time = time.time()
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

    def increment_missed_pings(self, client_addr) -> None:
        with self.lock:
            if client_addr in self.client_status:
                self.client_status[client_addr]["missed_pings_count"] += 1

    def get_inactive_clients(self, max_missed_pings: int) -> List[tuple]:
        with self.lock:
            inactive_clients = []
            for client_addr, status in self.client_status.items():
                if status["missed_pings_count"] >= max_missed_pings:
                    inactive_clients.append(client_addr)
            return inactive_clients

    def create_session(self, client_addr) -> str:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        with self.lock:
            self.sessions[session_id] = [client_addr]
        return session_id

    def get_session(self, session_id: str) -> Optional[List]:
        with self.lock:
            return self.sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        with self.lock:
            return session_id in self.sessions

    def join_session(self, session_id: str, client_addr) -> Tuple[bool, str]:
        with self.lock:
            if session_id not in self.sessions:
                return False, f"Sesja {session_id} nie istnieje"

            if client_addr in self.sessions[session_id]:
                return False, "Już jesteś w tej sesji"

            if len(self.sessions[session_id]) >= 2:
                return False, "Sesja jest pełna"

            self.sessions[session_id].append(client_addr)
            return True, f"Dołączono do sesji {session_id}"

    def remove_from_session(self, client_addr, session_id: str) -> bool:
        """Usuwa klienta z sesji i usuwa sesję, jeśli nie ma już uczestników."""
        with self.lock:
            participants = self.sessions.get(session_id)
            if not participants or client_addr not in participants:
                return False

            participants.remove(client_addr)
            if not participants:
                self.sessions.pop(session_id, None)

            return True

    def get_peer_connection(self, session_id: str, sender_addr):
        """Zwraca socket drugiego uczestnika sesji albo None."""
        with self.lock:
            participants = self.sessions.get(session_id)
            if not participants:
                return None

            for participant_addr in participants:
                if participant_addr != sender_addr:
                    return self.connections.get(participant_addr)

            return None

    def close_session_and_get_connections(self, session_id: str) -> List[object]:
        """Unieważnia sesje i zwraca aktywne sockety uczestnikow tej sesji."""
        with self.lock:
            participants = self.sessions.pop(session_id, None)
            if not participants:
                return []

            result = []
            for participant_addr in participants:
                conn = self.connections.get(participant_addr)
                if conn is not None:
                    result.append(conn)
            return result

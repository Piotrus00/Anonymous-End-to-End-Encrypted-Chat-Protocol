"""
Zarządzanie sesjami
"""

import threading
import uuid
from typing import Dict, List, Optional, Tuple


class SessionManager:
    """Zarządzanie sesjami: session_id -> lista adresów klientów."""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.connections: Dict[tuple, object] = {}
        self.lock = threading.Lock()

    def register_connection(self, client_addr, conn) -> None:
        with self.lock:
            self.connections[client_addr] = conn

    def unregister_connection(self, client_addr) -> None:
        with self.lock:
            self.connections.pop(client_addr, None)

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

"""
Zarządzanie sesjami
"""

import uuid
import threading
from typing import Dict, List


class SessionManager:
    """Zarządza sesją: session_id -> lista klientów"""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.lock = threading.Lock()

    def create_session(self, client_addr) -> str:
        """Tworzy nową sesję, zwraca session_id"""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

        with self.lock:
            self.sessions[session_id] = [client_addr]

        return session_id

    def get_session(self, session_id: str):
        """Pobiera sesję po ID"""
        with self.lock:
            return self.sessions.get(session_id)


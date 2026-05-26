"""
Zarządzanie sesjami
"""

import uuid
import threading
from typing import Dict, List, Optional, Tuple


class SessionManager:
    """Zarządza sesjami: session_id -> lista klientów"""

    def __init__(self):
        self.sessions: Dict[str, List] = {}
        self.lock = threading.Lock()

    def create_session(self, client_addr) -> str:
        """Tworzy nową sesję, zwraca session_id"""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

        with self.lock:
            self.sessions[session_id] = [client_addr]

        return session_id

    def get_session(self, session_id: str) -> Optional[List]:
        """Pobiera sesję po ID"""
        with self.lock:
            return self.sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        """Sprawdza czy sesja istnieje"""
        with self.lock:
            return session_id in self.sessions

    def join_session(self, session_id: str, client_addr) -> Tuple[bool, str]:
        """
        Próbuje dołączyć klienta do sesji.

        Args:
            session_id: ID sesji do dołączenia
            client_addr: Adres client'a

        Returns:
            (success, message) - success True jeśli dołączono, message zawiera szczegóły
        """
        with self.lock:
            # Sprawdzamy czy sesja istnieje
            if session_id not in self.sessions:
                return False, f"Sesja {session_id} nie istnieje"

            # Sprawdzamy czy klient już jest w sesji
            if client_addr in self.sessions[session_id]:
                return False, "Już jesteś w tej sesji"

            # Sprawdzamy czy sesja ma miejsce (max 2 klientów)
            if len(self.sessions[session_id]) >= 2:
                return False, "Sesja jest pełna"

            # Dodajemy klienta do sesji
            self.sessions[session_id].append(client_addr)
            return True, f"Dołączono do sesji {session_id}"


"""Przechowywanie JWT sesji po stronie klienta."""


class ClientAuthStore:
    def __init__(self) -> None:
        self.session_id: str | None = None
        self.token: str | None = None

    def set(self, session_id: str, token: str) -> None:
        self.session_id = session_id
        self.token = token

    @property
    def is_ready(self) -> bool:
        return bool(self.session_id and self.token)

    def require_token(self) -> str:
        if not self.token:
            raise RuntimeError("Brak tokenu JWT — wykonaj INIT lub JOIN")
        return self.token

import os

HOST = "127.0.0.1"
PORT = 65432
MAX_MESSAGE_SIZE = 8192
KEEP_ALIVE_INTERVAL = 3
MAX_MISSED_PINGS = 3
ACK_TIMEOUT = 10  # Czas w sekundach na oczekiwanie na ACK
RATE_LIMIT_MESSAGES = 5  # Max ilosc wiadomosci
RATE_LIMIT_WINDOW = 2    # W oknie czasowym (sekundy)

# TLS / WSS
TLS_ENABLED = os.environ.get("TLS_ENABLED", "true").lower() in ("1", "true", "yes")
TLS_CERT_FILE = os.environ.get("TLS_CERT_FILE", "certs/server.crt")
TLS_KEY_FILE = os.environ.get("TLS_KEY_FILE", "certs/server.key")
TLS_CA_FILE = os.environ.get("TLS_CA_FILE", TLS_CERT_FILE)
# Dla self-signed dev ustaw false; w produkcji true + prawdziwy CA
TLS_VERIFY = os.environ.get("TLS_VERIFY", "false").lower() in ("1", "true", "yes")

# JWT — w produkcji ustaw JWT_SECRET w zmiennej środowiskowej
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 86400  # 24h


def websocket_scheme() -> str:
    return "wss" if TLS_ENABLED else "ws"


def websocket_uri() -> str:
    return f"{websocket_scheme()}://{HOST}:{PORT}"


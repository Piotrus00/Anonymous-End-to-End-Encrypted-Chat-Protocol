import os

HOST = "127.0.0.1"
PORT = 65432
MAX_MESSAGE_SIZE = 8192
KEEP_ALIVE_INTERVAL = 3
MAX_MISSED_PINGS = 3
ACK_TIMEOUT = 10  # Czas w sekundach na oczekiwanie na ACK
RATE_LIMIT_MESSAGES = 5  # Max ilosc wiadomosci
RATE_LIMIT_WINDOW = 2    # W oknie czasowym (sekundy)

# JWT — w produkcji ustaw JWT_SECRET w zmiennej środowiskowej
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-insecure-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 86400  # 24h

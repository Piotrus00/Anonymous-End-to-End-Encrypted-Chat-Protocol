"""
Wspólny moduł do enkodowania/dekodowania wiadomości JSON
"""

import json
import socket
import struct
from typing import Tuple, Dict, Any


def read_exactly(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Odczytuje dokładnie `num_bytes` z gniazda.
    Blokuje, dopóki nie zbierze wymaganej liczby bajtów lub gniazdo nie zostanie zamknięte.
    """
    chunks = []
    bytes_recd = 0
    while bytes_recd < num_bytes:
        chunk = sock.recv(min(num_bytes - bytes_recd, 4096))
        if chunk == b'':
            raise ConnectionError("Socket connection broken")
        chunks.append(chunk)
        bytes_recd += len(chunk)
    return b''.join(chunks)


def decode_message(data: bytes) -> Tuple[bool, Dict[str, Any]]:
    """
    Dekoduje wiadomość z bajtów na słownik JSON.

    Returns:
        (success, message_dict) - success True jeśli dekodowanie się powiodło
    """
    try:
        message_str = data.decode('utf-8')
        message_json = json.loads(message_str)
        return True, message_json
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, {}


def encode_message(message: Dict[str, Any]) -> bytes:
    """Koduje słownik na JSON, dodaje 4-bajtowy nagłówek z długością i zwraca bajty"""
    message_bytes = json.dumps(message).encode('utf-8')
    # 'I' oznacza 4-bajtowy unsigned int, '!' to porządek sieciowy (big-endian)
    header = struct.pack('!I', len(message_bytes))
    return header + message_bytes

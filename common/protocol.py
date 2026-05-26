"""
Wspólny moduł do enkodowania/dekodowania wiadomości JSON
"""

import json
from typing import Tuple, Dict, Any


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
    """Koduje słownik na JSON i zwraca bajty"""
    return json.dumps(message).encode('utf-8')


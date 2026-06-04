"""Szyfrowanie end-to-end: X25519 (wymiana kluczy) + AES-GCM (treść wiadomości)."""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

HKDF_INFO = b"anon-chat-e2ee-v1"
NONCE_SIZE = 12


class CryptoSession:
    """Sesja kryptograficzna klienta — serwer nie ma dostępu do kluczy prywatnych."""

    def __init__(self) -> None:
        self._private_key = X25519PrivateKey.generate()
        self._aes_key: bytes | None = None

    def public_key_b64(self) -> str:
        raw = self._private_key.public_key().public_bytes_raw()
        return base64.b64encode(raw).decode("ascii")

    def set_peer_public_key(self, public_key_b64: str) -> None:
        raw = base64.b64decode(public_key_b64)
        peer_public_key = X25519PublicKey.from_public_bytes(raw)
        shared_secret = self._private_key.exchange(peer_public_key)
        self._aes_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=HKDF_INFO,
        ).derive(shared_secret)

    @property
    def is_ready(self) -> bool:
        return self._aes_key is not None

    def encrypt(self, plaintext: str) -> str:
        if self._aes_key is None:
            raise RuntimeError("Sesja szyfrowania nie jest gotowa — brak klucza peer-a")

        nonce = os.urandom(NONCE_SIZE)
        ciphertext = AESGCM(self._aes_key).encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        if self._aes_key is None:
            raise RuntimeError("Sesja szyfrowania nie jest gotowa — brak klucza peer-a")

        data = base64.b64decode(ciphertext_b64)
        nonce, ciphertext = data[:NONCE_SIZE], data[NONCE_SIZE:]
        plaintext = AESGCM(self._aes_key).decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")

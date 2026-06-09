"""TLS / WSS — konteksty SSL dla serwera i klienta."""

from __future__ import annotations

import datetime
import ipaddress
import ssl
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from .config import TLS_CA_FILE, TLS_CERT_FILE, TLS_KEY_FILE, TLS_VERIFY


def _cert_paths_exist() -> bool:
    return Path(TLS_CERT_FILE).is_file() and Path(TLS_KEY_FILE).is_file()


def ensure_dev_certificates() -> None:
    """Generuje self-signed certyfikat dev, jeśli brakuje plików w certs/."""
    if _cert_paths_exist():
        return

    cert_path = Path(TLS_CERT_FILE)
    key_path = Path(TLS_KEY_FILE)
    cert_path.parent.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Anonymous Chat Dev"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
    )
    certificate = cert_builder.sign(key, hashes.SHA256())

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    print(f"[TLS] Wygenerowano certyfikat dev: {cert_path}")


def create_server_ssl_context() -> ssl.SSLContext:
    """Kontekst TLS dla serwera WSS."""
    ensure_dev_certificates()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=TLS_CERT_FILE, keyfile=TLS_KEY_FILE)
    return context


def create_client_ssl_context() -> ssl.SSLContext | None:
    """Kontekst TLS dla klienta WSS. None gdy TLS wyłączone."""
    if TLS_VERIFY:
        context = ssl.create_default_context(cafile=TLS_CA_FILE)
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        # Self-signed dev — szyfrowanie włączone, weryfikacja certyfikatu wyłączona
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context

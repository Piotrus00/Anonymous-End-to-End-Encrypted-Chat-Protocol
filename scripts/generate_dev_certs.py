"""Generuje self-signed certyfikat dev do TLS (WSS)."""

from common.tls import ensure_dev_certificates

if __name__ == "__main__":
    ensure_dev_certificates()
    print("Certyfikaty gotowe w certs/")

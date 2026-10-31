"""Sicherheitsheader für alle Antworten, auch für Fehlerantworten."""

from __future__ import annotations

from typing import Final

LOCAL_HOST: Final = "127.0.0.1"
# Schutz gegen DNS-Rebinding: nur Anfragen an den eigenen Rechner werden beantwortet.
ALLOWED_HOSTS: Final = (LOCAL_HOST, "localhost")

CONTENT_SECURITY_POLICY: Final = "; ".join(
    (
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    )
)
SECURITY_HEADERS: Final = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}
# Antworten der Schnittstelle werden nie zwischengespeichert.
NO_STORE: Final = {"Cache-Control": "no-store"}

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

# Methoden, die nichts ändern; alle anderen verlangen einen passenden Origin (siehe unten).
SAFE_METHODS: Final = frozenset({"GET", "HEAD", "OPTIONS"})


def allowed_origins(port: int) -> frozenset[str]:
    """Die Ursprünge, von denen die Oberfläche Änderungen auslösen darf: die eigene Adresse."""
    return frozenset(f"http://{host}:{port}" for host in ALLOWED_HOSTS)


def is_allowed_request(method: str, origin: str | None, port: int) -> bool:
    """Prüft, ob eine Anfrage zulässig ist (Schutz vor Anfragen fremder Webseiten).

    Zustandsändernde Anfragen (POST, DELETE, …) sind nur ohne `Origin`-Header (kein Browser, z. B.
    Skript oder Test) oder mit der eigenen Adresse als `Origin` zulässig. Browser senden `Origin`
    bei solchen Anfragen immer; eine fremde Webseite kann den Header nicht fälschen.
    """
    if method.upper() in SAFE_METHODS or origin is None:
        return True
    return origin in allowed_origins(port)

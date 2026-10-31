# Testbericht

Nachweis pro Phase (UMSETZUNGSPLAN Abschnitt 10, docs/engineering-guidelines.md).

## Phase 0: Grundgerüst (31.10.2026)

Umsetzung: Commit `9f7d53a`. Umgebung: macOS, Python 3.13.3, Node.js 22.22.2, uv 0.11.14. Guide `b7ac158` (Branch `next`), XSD `73b337e`.

### Prüfbefehl

`uv run python scripts/check.py --hook`: **grün**, rund 11 s. Alle 14 Schritte OK: Arbeitsverzeichnis = Commit-Inhalt, `uv.lock` aktuell, ruff check, ruff format, mypy --strict (41 Dateien), pytest, npm ci, TypeScript, Biome, Vitest, Build, pip-audit (keine bekannten Lücken), npm audit (0 Lücken), Git-Hook aktiv. Der Git-Hook hat den Commit `9f7d53a` damit geprüft.

### Tests und Abdeckung

- pytest: **154 Tests bestanden**, davon 3 gegen den echten Guide-Klon. Abdeckung `app/core`: **99,6 %** (Mindestwert 90 %).
- Vitest: **34 Tests bestanden**, darunter der Prüftest „keine festen Texte im Frontend-Code“. Dass er anschlägt, wurde mit einer Probedatei nachgewiesen.
- `uv run python scripts/test.py`: bestanden; `guide-tested.json` mit `b7ac158` / `73b337e` geschrieben.

### Abnahme

| Kriterium | Ergebnis |
|---|---|
| `scripts/check.py` grün, vom Git-Hook vor jedem Commit ausgeführt | erfüllt |
| `scripts/test.py` läuft und schreibt `guide-tested.json` | erfüllt |
| App startet lokal, zeigt den Guide-Commit, liest die Mappingtabelle | erfüllt: `start.py` gestartet, `/api/guide` liefert Branch `next`, Commit `b7ac158`, XSD vorhanden, 8 Blätter gelesen; Bildschirmfoto der Oberfläche (Headless-Chrome) zeigt Guide-Status-Box und Legende, die CSP blockiert nichts |
| Fehlende XSD bzw. abweichender Stand werden gemeldet | erfüllt: Unit-Tests mit synthetischem Guide-Klon; „weicht ab“ zusätzlich live mit verändertem `guide-tested.json` geprüft. Gemeldet wird „weicht ab“, nicht „neuer“ (Entscheid „Guide-Stand ohne Datum“). |

### Code-Review (eingebaute Prüfung `/code-review`, Stufe high)

10 Funde, alle behoben, bevor `9f7d53a` committet wurde:

1. `test.py` schrieb den Nachweis auch bei Teilläufen. Jetzt nur noch ohne eigene pytest-Argumente.
2. Lesefehler in einem Excel-Blatt brachen den Start ab. Jetzt erscheint die Meldung `mapping.file_unreadable`.
3. Tief verschachteltes JSON (RecursionError) brach das Laden ab. Jetzt erscheint eine Meldung.
4. `defusedxml` war nur zufällig vorhanden. Jetzt ist es eine Laufzeitabhängigkeit, und ein Test prüft das.
5. Die Meldung „weicht ab“ nannte den XSD-Commit nicht. Jetzt nennt sie Guide- und XSD-Commit.
6. Fehlerantworten (500) hatten keine Sicherheitsheader. Jetzt setzt `error_response` sie.
7. Der Hook prüfte das Arbeitsverzeichnis statt des Commit-Inhalts. Jetzt verlangt `--hook`, dass alles vorgemerkt ist.
8. Der Port des Vite-Proxys war fest eingetragen. Jetzt kommt er aus `config/settings.json`.
9. Doppelter Code (npm-Prüfung, Commit-Format) liegt jetzt in `scripts/frontend.py` bzw. `is_commit_id`.
10. Eine fehlende Farbe wurde als „ungültig“ gemeldet. Jetzt gilt still der Standardwert, wie bei `settings.json`.

### Sicherheits-Review (eingebaute Prüfung `/security-review`)

Über `ca6df22..9f7d53a`: **keine Funde** mit hoher Sicherheit. Geprüft: Git-Lesen (Pfadprüfung der Referenzen), XML im Excel-Paket (defusedxml), JSON-Einstellungen, Server (nur 127.0.0.1, Host-Prüfung, kein CORS, keine Swagger-Seite, Fehler ohne Details, strenge CSP, StaticFiles), Oberfläche (kein `dangerouslySetInnerHTML`), Skripte (Unterprozesse ohne Shell).

Die eingebaute Prüfung vergleicht mit `origin/HEAD`. Das Repository hat kein Remote, deshalb wurde für das Review vorübergehend eine lokale Referenz `refs/remotes/origin/HEAD` auf `ca6df22` angelegt und danach gelöscht.

Zusätzlicher Fund aus der Prüfung der Testdateien: lxml stürzt bei der Schema-Prüfung von `fixtures/security_xxe.xml` ab. Daraus folgt, dass Dateien mit `DOCTYPE` in Phase 4 vor lxml abgewiesen werden müssen (offener Punkt 4).

### Lücken

- Windows: nicht getestet (`start.ps1` vorhanden).
- `pip-audit` und `npm audit` brauchen Internet. Ohne Verbindung ist der Prüfbefehl nicht grün, und es lässt sich nicht committen.
- Offen vor Phase 3: Welcher `TimingLink` gilt (`OnwardTimingLinkRef`, docs/open-points.md Punkt 3).

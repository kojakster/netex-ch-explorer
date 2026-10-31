# Lokale Schnittstelle (JSON)

Vertrag zwischen Server (`app/server`) und Oberfläche (`app/frontend/src/api.ts`, Typen in `types.ts`). Stand: Phase 0.

## Allgemein

- Server nur auf `127.0.0.1`. Anfragen mit anderem `Host` als `127.0.0.1` oder `localhost` werden mit 400 abgewiesen (Schutz gegen DNS-Rebinding).
- Die Oberfläche wird vom selben Server ausgeliefert (gleicher Ursprung); deshalb ist **kein CORS** eingerichtet. Im Entwicklungsmodus leitet Vite `/api` an den Server weiter.
- Feldnamen in camelCase. Texte nie im Klartext, sondern als **Übersetzungsschlüssel mit Parametern** (`key`, `params`); die Oberfläche setzt den Text aus `de-CH.json` bzw. `en.json` ein.
- Antworten der Schnittstelle tragen `Cache-Control: no-store`. Alle Antworten tragen Sicherheitsheader (Content-Security-Policy, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
- Keine Swagger-/OpenAPI-Seite (sie würde Ressourcen aus dem Internet laden).

### Fehlerformat

Jeder Fehler hat dieselbe Form, ohne interne Details (keine Stacktraces):

```json
{ "error": { "key": "error.not_found", "params": {} } }
```

| Schlüssel | HTTP | Bedeutung |
|---|---|---|
| `error.not_found` | 404 | Pfad unbekannt |
| `error.method_not_allowed` | 405 | Methode nicht erlaubt |
| `error.invalid_request` | 422 | Ungültige Parameter |
| `error.http` | andere 4xx/5xx | Allgemeiner HTTP-Fehler |
| `error.internal` | 500 | Programmfehler (Details nur im Serverprotokoll) |

### Meldung (`Issue`)

```json
{ "severity": "error | warning | info", "key": "guide.xsd_missing", "params": { "file": "…", "command": "…" } }
```

Alle Schlüssel des Kerns stehen in `app/core/messages.py` (`MessageKey`), die der Fehlerantworten in `app/server/errors.py` (`ErrorKey`). Ein Test prüft, dass jeder Schlüssel in jeder Sprachdatei steht.

## Umgesetzt

### `GET /api/guide`

Guide-Status für die Guide-Status-Box. Wird beim Start einmal ermittelt; nach einem Guide-Update den Server neu starten.

```json
{
  "path": "/…/netexRealisationGuideSwitzerland",
  "found": true,
  "branch": "next",
  "commit": "b7ac15860369818a8fb53c64ed6f71318f019380",
  "xsdCommit": "73b337e22ceed7905a1be14e4e506f1afa359b54",
  "xsdPresent": true,
  "testState": "tested | differs | never_tested | unknown",
  "testedCommit": "b7ac15860369818a8fb53c64ed6f71318f019380",
  "mappingSheets": [{ "name": "StopUse", "headerRow": 3, "rows": 4 }],
  "issues": []
}
```

- `branch` ist `null` bei losgelöstem HEAD; `commit`/`xsdCommit` sind `null`, wenn nicht bestimmbar.
- Kein Commit-Datum (Entscheid „Guide-Stand ohne Datum“). `testState` `differs` heisst „weicht vom zuletzt getesteten Stand ab“ (Guide- oder XSD-Commit).
- Mögliche Meldungen: `guide.not_found`, `guide.not_git`, `guide.git_unreadable`, `guide.xsd_missing`, `guide.never_tested`, `guide.tested_differs`, `guide.test_record_invalid`, `mapping.*`.

### `GET /api/app`

Daten für Farblegende, Hilfeseite und Sprache. Ergänzt den Plan (Abschnitt 5), weil Legende und Hilfeseite die Werte aus `config/` und den Listen des Kerns brauchen.

```json
{
  "language": "de-CH",
  "languages": ["de-CH", "en"],
  "frameColors": [{ "key": "TimetableFrame", "background": "#0057B8", "text": "#FFFFFF" }],
  "notRelevantElements": ["SiteFacilitySet"],
  "features": ["guide_status", "frame_legend", "language_switch", "help_page"],
  "checks": [{ "id": "xsd", "status": "performed | not_implemented | deferred", "sources": ["xsd/xsd/NeTEx_publication.xsd"] }],
  "severities": ["error", "warning", "info"],
  "issues": []
}
```

- `frameColors`: Reihenfolge und Schlüssel fest; `unknown` = unbekannter Frame, `notRelevant` = Grau.
- `issues`: Meldungen beim Laden von `config/` (`config.*`).

## Geplant (Plan Abschnitt 5)

`POST /api/datasets`, `GET /api/datasets/{id}`, `GET /api/datasets/{id}/journeys`, `GET /api/datasets/{id}/objects`, `GET /api/objects/{id}`, `GET /api/objects/{id}/xml`, `GET /api/journeys/{id}`, `GET /api/datasets/{id}/diagnostics`, `POST /api/datasets/{id}/validate`. Werden mit den Phasen 1–4 hier beschrieben.

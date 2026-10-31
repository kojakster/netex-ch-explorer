# Lokale Schnittstelle (JSON)

Vertrag zwischen Server (`app/server`) und Oberfläche (`app/frontend/src/api.ts`, Typen in `types.ts`). Stand: Phase 1.

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
  "examples": [
    {
      "name": "01_NeTEx_Spiez_Interlaken_Ost.xml",
      "title": "Basic train with TimeDemandType",
      "result": "clean | notes | errors | unreadable",
      "counts": { "error": 0 },
      "change": "unchanged | changed | new | untested"
    }
  ],
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

### IDs

Datensätze haben eine zufällige ID (nicht erratbar). Objekte und alle anderen Elemente haben die ID `<Datensatz-ID>.<Elementnummer>`; jedes Element ist damit einzeln abrufbar (z. B. eine Eigenschaft eines Objekts für die Markierung im XML). Unbekannte oder ungültige IDs ergeben 404. Der Server hält höchstens 10 Datensätze offen.

### `POST /api/datasets`

Öffnet ein Beispiel des Guides. Nur Dateinamen aus der Beispielliste von `GET /api/guide`; keine Pfade.

```json
{ "example": "01_NeTEx_Spiez_Interlaken_Ost.xml" }
```

Antwort (auch `GET /api/datasets/{id}`):

```json
{
  "id": "Zuf4ll1g3-ID",
  "files": [{ "id": 1, "name": "01_….xml", "size": 16651, "sha256": "…", "readable": true, "elements": 278, "objects": 47 }],
  "objectTypes": [{ "name": "Quay", "count": 3 }],
  "frames": [Objekt, …],
  "diagnosticCounts": { "error": 0, "warning": 0, "info": 0 }
}
```

**Objekt** (in allen Antworten gleich):

```json
{
  "id": "Zuf4ll1g3-ID.37", "name": "Quay", "xmlId": "ch:1:sloid:7483:0:90840", "version": "1",
  "label": null, "fileName": "01_….xml", "line": 115, "column": 9,
  "frame": { "objectId": "Zuf4ll1g3-ID.36", "name": "SiteFrame", "xmlId": "ch:1:SiteFrame:j26" },
  "colorKey": "SiteFrame | … | unknown | notRelevant | null", "notRelevant": false
}
```

### `GET /api/datasets/{id}/journeys`

Fahrten (`ServiceJourney`, `TemplateServiceJourney`) mit `trainNumbers`, `departureTime`, `departureDayOffset`, `line`, `firstStop`, `lastStop`. Jede Angabe: `{ "status": "found | absent | not_resolved | ambiguous", "text": "…", "objectId": "…" }`. `text` ist bei `not_resolved`/`ambiguous` die gesuchte Referenz; `objectId` zeigt auf die Herkunft (Element der Angabe bzw. die Referenz).

### `GET /api/datasets/{id}/objects?type=&q=&limit=&offset=`

Einfache Objektsuche: `type` = Elementname, `q` = Teiltext in ID oder Name (ohne Gross-/Kleinschreibung, höchstens 200 Zeichen), `limit` 1–200 (Standard 50), `offset` ≥ 0. Antwort `{ "total": 3, "items": [Objekt, …] }`.

### `GET /api/objects/{id}`

```json
{ "object": Objekt, "path": "/PublicationDelivery/…/StopPlace[1]/quays/Quay",
  "attributes": { "id": "…", "version": "1" },
  "properties": [{ "id": "…", "name": "PublicCode", "attributes": {}, "text": "8", "line": 130, "column": 10, "children": [] }],
  "truncated": false }
```

`text` ist der direkte Textinhalt, unverändert (auch Leerzeichen). Positionsnummern im Pfad nur bei gleichnamigen Geschwistern. Höchstens 2000 Elemente, sonst `truncated`.

### `GET /api/objects/{id}/xml` und `GET /api/datasets/{id}/xml?file=&line=&column=`

XML-Ausschnitt um ein Element bzw. um eine Stelle (z. B. einer Diagnose), 30 Zeilen Kontext, höchstens 2000 Zeilen.

```json
{ "fileName": "01_….xml", "firstLine": 85, "text": "…", "focusFrom": 812, "focusTo": 1190,
  "frames": [{ "objectId": "…", "name": "SiteFrame", "xmlId": "…", "colorKey": "SiteFrame", "fromLine": 85, "toLine": 157 }],
  "truncated": false }
```

`focusFrom`/`focusTo` sind Zeichen-Offsets in `text` (Element vom `<` bis nach dem schliessenden `>`). `frames` enthält alle Frames im Ausschnitt; der innerste gilt.

### `GET /api/datasets/{id}/diagnostics?category=&severity=`

```json
[{ "category": "xml_syntax", "severity": "error", "key": "xml.syntax_error", "params": { "detail": "mismatched tag" },
   "fileId": 1, "fileName": "broken_xml.xml", "line": 48, "column": 34 }]
```

Arten: `file`, `xml_syntax`, `xsd`, `profile_rule`, `reference`, `projection`. In Phase 1 entstehen nur `file` (Zeichenkodierung) und `xml_syntax` (Syntaxfehler, `DOCTYPE`).

## Geplant

`POST /api/datasets` für eigene Dateien (XML, mehrere XML, ZIP) und `POST /api/datasets/{id}/validate` folgen in Phase 4; Referenzen ein-/ausgehend im Objektdetail in Phase 2; `GET /api/journeys/{id}` (Fahrtansicht) in Phase 3.

# Lokale Schnittstelle (JSON)

Vertrag zwischen Server (`app/server`) und Oberfläche (`app/frontend/src/api.ts`, Typen in `types.ts`). Stand: Phase 3.

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

Fahrten (`ServiceJourney`, `TemplateServiceJourney`) mit `trainNumbers`, `departureTime`, `departureDayOffset`, `line`, `firstStop`, `lastStop`. Jede Angabe: `{ "status": "found | absent | not_resolved | ambiguous | external_or_unloaded", "text": "…", "objectId": "…" }`. `text` ist bei `not_resolved`/`ambiguous` die gesuchte Referenz; `objectId` zeigt auf die Herkunft (Element der Angabe bzw. die Referenz).

### `GET /api/datasets/{id}/objects?type=&q=&limit=&offset=`

Einfache Objektsuche: `type` = Elementname, `q` = Teiltext in ID oder Name (ohne Gross-/Kleinschreibung, höchstens 200 Zeichen), `limit` 1–200 (Standard 50), `offset` ≥ 0. Antwort `{ "total": 3, "items": [Objekt, …] }`.

### `GET /api/objects/{id}`

```json
{ "object": Objekt, "path": "/PublicationDelivery/…/StopPlace[1]/quays/Quay",
  "attributes": { "id": "…", "version": "1" },
  "properties": [{ "id": "…", "name": "PublicCode", "attributes": {}, "text": "8", "line": 130, "column": 10,
                   "reference": null, "children": [] }],
  "truncated": false,
  "reference": null,
  "outgoing": [Verweis, …],
  "incoming": [Verweis, …],
  "referencesTruncated": false }
```

`text` ist der direkte Textinhalt, unverändert (auch Leerzeichen). Positionsnummern im Pfad nur bei gleichnamigen Geschwistern. Höchstens 2000 Elemente, sonst `truncated`.

**Referenzen** (Phase 2): `outgoing` = Verweise, die in diesem Objekt stehen (auch in `Extensions`; Verweise in verschachtelten Objekten gehören diesen); `incoming` = Verweise auf dieses Objekt (Rückwärtsreferenzen); `reference` = die eigene Referenz, wenn die abgerufene ID ein Ref-Element ist; `properties[].reference` = Status und Ziel eines Ref-Elements im Eigenschaftsbaum (`{ "status", "targetId", "expected" }`). Höchstens 500 Verweise je Richtung, sonst `referencesTruncated`.

**Verweis:**

```json
{ "element": Objekt (das Ref-Element), "ref": "ch:1:sloid:7483:0:90840", "refVersion": "1",
  "status": "resolved | unresolved | ambiguous | external_or_unloaded",
  "expected": ["Quay"], "target": Objekt | null, "owner": Objekt | null }
```

- `expected`: erwartete Zieltypen (`nameOfRefClass`, sonst `config/ref-targets.json`, sonst Name ohne `Ref`).
- Status: `resolved` (genau ein Ziel; bei mehreren entscheidet `version`/`versionRef`, ausser `any`), `unresolved` (Objekte des Typs vorhanden, `id` fehlt: ⚠ Fehler), `ambiguous` (mehrere Ziele: △ Warnung), `external_or_unloaded` (im Datensatz kein Objekt des Typs: ℹ Hinweis). Gleiche ID bei verschiedenen Typen (`Quay`/`ScheduledStopPoint`) wird über den Typ unterschieden.
- `target` nur bei `resolved`. `owner`: das Objekt, in dem der Verweis steht.

### `GET /api/objects/{id}/provenance`

Herkunftskette eines Elements: Frame, enthaltende Objekte, die Angabe selbst und bei einer aufgelösten Referenz das Ziel.

```json
[{ "kind": "frame", "object": Objekt }, { "kind": "object", "object": Objekt },
 { "kind": "element", "object": Objekt }, { "kind": "target", "object": Objekt }]
```

`kind`: `frame` (innerster Frame), `object` (Element mit `id`), `element` (Angabe ohne `id`, z. B. Eigenschaft oder Ref-Element), `target` (Ziel einer Referenz). Jedes Glied trägt die Farbe seines Frames (`colorKey`).

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

Arten: `file`, `xml_syntax`, `xsd`, `profile_rule`, `reference`, `projection`. Bisher entstehen `file` (Zeichenkodierung), `xml_syntax` (Syntaxfehler, `DOCTYPE`) und `reference` (Phase 2: `reference.unresolved` ⚠ Fehler, `reference.ambiguous` △ Warnung, `reference.external_or_unloaded` ℹ Hinweis, `reference.version_differs` ℹ Hinweis für eine aufgelöste Referenz mit abweichender Version; Parameter `element`, `ref`, `expected` bzw. bei `version_differs` `version` (Referenz) und `found` (Ziel); Stelle = das Ref-Element).

### `GET /api/journeys/{id}`

Fahrtansicht einer `ServiceJourney` oder `TemplateServiceJourney`. `{id}` ist die Objekt-ID der Fahrt (`<Datensatz-ID>.<Elementnummer>`, z. B. aus `GET /api/datasets/{id}/journeys`). Andere Elemente, unbekannte oder ungültige IDs ergeben 404. Regeln und Belege: [mapping.md](mapping.md); Annahmen: [assumptions.md](assumptions.md).

**Quelle** (`ObjectOut`, wie `object` in allen Antworten): Jede Angabe nennt ihr Element der Quelle mit Typ, `id`, Datei, Zeile/Spalte, Frame und `colorKey`. Die Oberfläche markiert damit die Stelle im XML und färbt die Angabe.

**Angabe** (`ValueOut`): `{ "status": "found | absent | not_resolved | ambiguous | external_or_unloaded", "text": "…", "element": Objekt | null }`. `text` ist bei `not_resolved`/`ambiguous`/`external_or_unloaded` die gesuchte Referenz.

```json
{
  "journey": Objekt,
  "guideCommit": "b7ac158…",
  "pattern": Angabe, "timeDemandType": Angabe,
  "trainNumbers": [Angabe], "line": Angabe,
  "privateCodes": [{ "codeType": "sjyid", "value": "…", "element": Objekt }],
  "transports": [{ "owner": Objekt, "role": "journey | line", "mode": Angabe, "submodeType": "RailSubmode", "submode": Angabe }],
  "categories": [{ "role": "journey | line", "ref": Objekt, "target": Objekt, "problem": Angabe,
                   "shortName": Angabe, "names": [{ "lang": "de", "text": "…", "element": Objekt }], "master": Stammdaten }],
  "validities": [{ "ref": Objekt, "days": Betriebstage, "problem": Angabe }],
  "stops": [Halt], "parts": [Teilstrecke], "facilities": [Angebotsmenge], "notices": [Hinweis],
  "diagnostics": [Diagnose]
}
```

- **Halt:** `position` (ab 1, XML-Reihenfolge), `point` (`StopPointInJourneyPattern`), `stopPoint` (Name des `ScheduledStopPoint`), `stopPlace` (Name der `StopPlace`), `quay` (`PublicCode` der Kante), `assignment` (`PassengerStopAssignment`), `forBoarding`, `forAlighting`, `requestStop` (Angaben), `stopUse` (Code mit Stammdaten), `arrival`/`departure` (Zeit; erster Halt ohne Ankunft, letzter ohne Abfahrt), `partNumbers` (Nummern der Teilstrecken, die den Halt einschliessen). Fehlt die Zuordnung zur Haltestelle, steht in `stopPlace`/`quay` der Status: `external_or_unloaded` („Haltestelle nicht in dieser Datei“, wenn die Datei keine `StopPlace` enthält) oder `absent`.
- **Zeit:** `id` (`arrival-<n>`/`departure-<n>`), `status` (`explicit` = steht in der Datei, `computed`, `not_computable`), `clock` (`hh:mm:ss`, `null` wenn nicht berechenbar), `dayOffset` (Tage ab Betriebstag, negativ möglich), `offsetOrigin` (`explicit` = `DepartureDayOffset` steht in der Datei, `default` = fehlt, 0 als Standardwert, `computed` = durch das Aufsummieren ein anderer Tag), `source` (Element der Zeit), `chain` (Rechenkette), `reason` (Grund bei `not_computable`: Schlüssel, Parameter, Element).
- **Rechenkette:** Liste von Summanden in der Reihenfolge der Rechnung: `kind` (`departure_time`, `day_offset`, `run_time`, `wait_time`), `value` (Text aus der Datei, `null` bei Standardwert), `default` (Standardwert: kein Element als Quelle), `seconds` (Summand), `clock`/`dayOffset` (Zwischenstand nach dem Summanden), `element` (Quelle), `related` (beteiligte Objekte: `TimingLink`, `JourneyRunTime` bzw. `JourneyWaitTime`), `viaFromTo` (der `TimingLink` wurde über `FromPointRef`/`ToPointRef` bestimmt).
- **Betriebstage:** `condition`, `fromDate`/`toDate`/`validDayBits` (Elemente), `firstDay`/`lastDay` (ISO-Datum), `periodDays`, `validCount` (Anzahl Bits `1`), `days` (gültige Tage als ISO-Datum; leer, wenn `daysListed` falsch ist), `findings` (Probleme).
- **Stammdaten** (`master`): `{ "status": "found | none | unavailable", "matches": [{ "sheet": "Angebote", "row": 115, "texts": [{ "label": "Angebottext", "text": "1. Klasse" }] }] }`. `none` = „keine Erläuterung in den Stammdaten“, `unavailable` = Blatt oder Spalte der Mappingtabelle fehlt. Den Guide-Stand nennt `guideCommit`.
- **Teilstrecke** (`JourneyPart`): `number`, `element`, `description`, `purpose`, `trainNumbers`, `parentJourney`, `startStop`/`endStop` (`stop` = Name, `position` = Halt dieser Fahrt oder `null`), `start`/`end` (`time`, `dayOffset`, `clock`, `day`), `facilities`, `validity`, `category`.
- **Angebotsmenge** (`ServiceFacilitySet`): `ref`, `facilitySet`, `problem`, `description`, `groups` (je Gruppe `element` und `codes` mit Quelle und Stammdaten).
- **Hinweis:** `assignment`, `scope` (`journey`, `pattern`, `stop`, `journey_ref`, `pattern_ref`), `notice`, `shortCode`, `noticeType`, `texts` (alle Fassungen, `alternativeFor` bei `AlternativeText`), `startPosition`/`endPosition` (Halte dieser Fahrt), `validity`.
- **Diagnosen** (Art `projection`): wie in `GET /api/datasets/{id}/diagnostics`, aber nur für diese Fahrt und bei Abruf berechnet. Schlüssel: `projection.time.*` (Zeit nicht berechenbar, △ Warnung), `projection.timing_link_from_to`, `projection.day_offset_default`, `projection.stop_order_differs`, `projection.dst_night_forward`/`_back` (ℹ Hinweise), `projection.part_time_differs`, `projection.availability_*` (△ Warnungen), `projection.notice_unassigned` (ℹ Hinweis, ohne Stelle). Sie zählen nicht in `diagnosticCounts` und erscheinen nicht in der Diagnosenliste des Datensatzes.

## Geplant

`POST /api/datasets` für eigene Dateien (XML, mehrere XML, ZIP) und `POST /api/datasets/{id}/validate` folgen in Phase 4.

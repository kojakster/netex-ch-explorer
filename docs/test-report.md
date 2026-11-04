# Testbericht

Nachweis pro Phase (UMSETZUNGSPLAN Abschnitt 10, docs/engineering-guidelines.md).

## Phase 0: Grundgerüst (31.10.2026)

Umsetzung: Commit `b6b3d9b`. Umgebung: macOS, Python 3.13.3, Node.js 22.22.2, uv 0.11.14. Guide `b7ac158` (Branch `next`), XSD `73b337e`.

### Prüfbefehl

`uv run python scripts/check.py --hook`: **grün**, rund 11 s. Alle 14 Schritte OK: Arbeitsverzeichnis = Commit-Inhalt, `uv.lock` aktuell, ruff check, ruff format, mypy --strict (41 Dateien), pytest, npm ci, TypeScript, Biome, Vitest, Build, pip-audit (keine bekannten Lücken), npm audit (0 Lücken), Git-Hook aktiv. Der Git-Hook hat den Commit `b6b3d9b` damit geprüft.

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

10 Funde, alle behoben, bevor `b6b3d9b` committet wurde:

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

Über `ab1f0a3..b6b3d9b`: **keine Funde** mit hoher Sicherheit. Geprüft: Git-Lesen (Pfadprüfung der Referenzen), XML im Excel-Paket (defusedxml), JSON-Einstellungen, Server (nur 127.0.0.1, Host-Prüfung, kein CORS, keine Swagger-Seite, Fehler ohne Details, strenge CSP, StaticFiles), Oberfläche (kein `dangerouslySetInnerHTML`), Skripte (Unterprozesse ohne Shell).

Die eingebaute Prüfung vergleicht mit `origin/HEAD`. Das Repository hat kein Remote, deshalb wurde für das Review vorübergehend eine lokale Referenz `refs/remotes/origin/HEAD` auf `ab1f0a3` angelegt und danach gelöscht.

Zusätzlicher Fund aus der Prüfung der Testdateien: lxml stürzt bei der Schema-Prüfung von `fixtures/security_xxe.xml` ab. Daraus folgt, dass Dateien mit `DOCTYPE` in Phase 4 vor lxml abgewiesen werden müssen (offener Punkt 4).

### Lücken

- Windows: nicht getestet (`start.ps1` vorhanden).
- `pip-audit` und `npm audit` brauchen Internet. Ohne Verbindung ist der Prüfbefehl nicht grün, und es lässt sich nicht committen.
- Offen vor Phase 3: Welcher `TimingLink` gilt (`OnwardTimingLinkRef`, docs/open-points.md Punkt 3).

## Phase 1: Einlesen und Objekt-Explorer (31.10.2026)

Umsetzung: Commits `936a249` und `834e262` (Funde aus dem Code-Review). Umgebung wie Phase 0. Guide `b7ac158`, XSD `73b337e`.

### Prüfbefehl

`uv run python scripts/check.py --hook`: **grün** bei beiden Commits (Git-Hook). Alle 14 Schritte OK, pip-audit und npm audit ohne Lücken.

### Tests und Abdeckung

- pytest: **266 Tests bestanden**, davon 25 gegen den Guide-Klon (alle 22 Beispiele einzeln geladen, Beispiel 01 fachlich). Abdeckung `app/core`: **98 %**.
- Vitest: **50 Tests bestanden** (u. a. App-Ablauf Beispiel → Fahrt → Objekt → XML, CodeMirror-Markierung und Frame-Beschriftung, verworfene ältere Antworten).
- `scripts/test.py`: bestanden; `guide-tested.json` (Schema 2) mit Prüfsumme und Ergebnis für 22 Beispiele, alle „ohne Meldungen“.

### Abnahme

| Kriterium | Ergebnis |
|---|---|
| Alle Guide-Beispiele laden ohne Absturz | erfüllt: parametrisierter Test über alle 22 Beispiele; bei jedem Objekt beginnt der markierte Ausschnitt mit `<` und endet mit `>` |
| ID-Suche zeigt Objekt mit Frame, Datei, Zeile/Spalte | erfüllt: im Browser (Chrome, Playwright aus dem Scratchpad) Suche `ch:1:sloid:7483:0:90840` in Beispiel 01 → 2 Treffer (`Quay`, `ScheduledStopPoint` getrennt); `Quay` zeigt `SiteFrame`, Zeile 115, Spalte 9, Pfad |
| Klick markiert exakt die Stelle | erfüllt: Markierung beginnt bei `<Quay id=…`; Klick auf `DepartureTime` markiert genau `<DepartureTime>10:35:00</DepartureTime>`; Frame-Bänder und Frame-Namen am Rand; keine Meldungen in der Browser-Konsole |
| Beispielauswahl mit Status pro Beispiel, Prüfsummen in `guide-tested.json` | erfüllt |

### Code-Review (eingebaute Prüfung `/code-review`, Stufe high, über `3c92ae8..936a249`)

10 Funde, alle behoben in `834e262`:

1. Markierung bei CRLF-Dateien (Beispiel 15) und Zeichen ausserhalb der Basisebene verschoben. Jetzt Zeilenumbrüche LF und Offsets in UTF-16-Einheiten, Test mit CRLF und Emoji.
2. UTF-16/32 wurde nicht abgewiesen. Jetzt Diagnose „nicht unterstützt“.
3. Schnelles Umschalten der Beispiele: Eine ältere Antwort konnte die neuere überschreiben. Jetzt wird sie verworfen.
4. Verdrängte Datensätze wurden während laufender Anfragen geschlossen (500). Jetzt nicht mehr ausdrücklich geschlossen.
5. Elemente ohne Ende zeigten keine Kinder. Jetzt Nachfahren über die Tiefe.
6. Nicht aufgelöste Zugnummern erschienen wie Zugnummern. Jetzt mit Status und Herkunft.
7. `DepartureDayOffset` fehlte in der Liste. Jetzt angezeigt.
8. Sehr grosse Zahlen führten zu 500. Jetzt Obergrenzen (422).
9. Suche ohne Gross-/Kleinschreibung nur für ASCII. Jetzt `casefold`, ID und Name getrennt (ein Treffer über die Feldgrenze ist nicht mehr möglich).
10. Die Zeilentabelle wurde bei jedem Ausschnitt neu berechnet. Jetzt zwischengespeichert.

### Sicherheits-Review (eingebaute Prüfung `/security-review`, über `3c92ae8..834e262`)

**Keine Funde.** Geprüft: Path Traversal beim Öffnen von Beispielen (nur Namen aus der Beispielliste), XXE (`DOCTYPE` abgewiesen), SQL (nur feste Teile, Werte als Parameter), IDs (zufällig, Format geprüft), XSS (kein `innerHTML`, CodeMirror-Beschriftungen über `textContent`). Vorübergehende lokale Referenz `origin/HEAD` wie in Phase 0, danach gelöscht.

Eigener Fund bei der Browser-Prüfung: Die strenge CSP blockierte die Stile von CodeMirror (`<style>`-Element). Gelöst ohne CSP-Lockerung durch einen Shadow-DOM (Entscheid „Umsetzung Phase 1“, Punkt 6).

### Lücken und Hinweise

- Referenzen nur als Grundstufe (Phase 2: Versionen, Rückwärtsreferenzen, `external_or_unloaded`, Referenzdiagnosen).
- Der Build meldet ein Skriptpaket über 500 kB (CodeMirror). Für die lokale Nutzung unkritisch; bei der Webversion prüfen.
- Dateien mit nur CR als Zeilenumbruch (ohne LF) werden in den Zeilennummern nicht unterstützt; in der Praxis nicht anzutreffen.
- Windows: nicht getestet.

## Phase 2: Referenzen und Herkunft (31.10.2026)

Umsetzung: Commits `e7c8bae` und `3aa9219` (Funde aus dem Code-Review). Umgebung wie Phase 0. Guide `b7ac158`, XSD `73b337e`.

### Prüfbefehl

`uv run python scripts/check.py --hook`: **grün** bei beiden Commits (Git-Hook). Alle 14 Schritte OK, pip-audit und npm audit ohne Lücken.

### Tests und Abdeckung

- pytest: **311 Tests bestanden**, davon 28 gegen den Guide-Klon (alle 22 Beispiele einzeln geladen, Beispiel 01 fachlich, Zieltyp-Liste gegen XSD und Beispiele). Abdeckung `app/core`: **98 %**.
- Vitest: **63 Tests bestanden** (u. a. Verweis folgen, Zurück/Vor im Verlauf, Sprung aus dem Eigenschaftsbaum, Herkunftskette, Ausblenden der Kette bei Diagnosen).
- `scripts/test.py`: bestanden; `guide-tested.json` neu geschrieben: 21 Beispiele „ohne Meldungen“, Beispiel 17 „mit Hinweisen“ (4× `external_or_unloaded`).

### Abnahme

| Kriterium | Ergebnis |
|---|---|
| Referenzen inkl. `Extensions`, Auflösung über ID + Typ | erfüllt: alle Elemente mit `ref` an beliebiger Stelle; Test mit Verweisen in `Extensions`; 1520 Referenzen der 22 Beispiele: 1516 aufgelöst, 4 `external_or_unloaded`, keine nicht auflösbaren |
| `Quay` und `ScheduledStopPoint` mit gleicher ID werden unterschieden | erfüllt: Test an `ch20_three_stops.xml`; im Browser (Chrome, Playwright aus dem Scratchpad) Beispiel 01: `Quay` hat nur `QuayRef` als eingehenden Verweis, `ScheduledStopPoint` zusätzlich `FromPointRef` und `ScheduledStopPointRef` |
| Rückwärtsreferenzen, Herkunftsanzeige, Frame-Farben | erfüllt: eingehende und ausgehende Verweise als Liste mit Frame-Farbe der Gegenseite, Herkunftskette als farbige Kästchen (anklickbar), Status im Eigenschaftsbaum |
| Navigation vor/zurück | erfüllt: im Browser Verweis gefolgt, „Zurück im Verlauf“ führt zum vorherigen Objekt; Vitest-Test für Vor und Zurück |
| Nicht auflösbare Referenzen als Diagnose | erfüllt: `reference.unresolved` (⚠ Fehler), `reference.ambiguous` (△ Warnung), `reference.external_or_unloaded` (ℹ Hinweis) mit Stelle; Beispiel 17 im Browser: 4 Hinweise, Klick markiert die Stelle im XML; Keine Meldungen in der Browser-Konsole |
| Hilfeseite nachgeführt | erfüllt: Funktionen „Referenzen“, „Herkunftskette“, „Verlauf“, Prüfschritt „Referenzen“ jetzt „durchgeführt“, beide Sprachdateien; Test `tests/test_help_texts.py` |

### Wichtigster Befund der Phase

Mit „Zieltyp = Name ohne `Ref`“ blieben 125 von 1520 Referenzen der Beispiele unaufgelöst, obwohl das Ziel in der Datei steht (z. B. `ResponsibleOrganisationRef` → `Operator`). Gelöst mit `config/ref-targets.json` (16 Einträge, Entscheid vom Benutzer); ein Test prüft die Einträge gegen die XSD und meldet fehlende Einträge für die Beispiele. Zwei Fälle fielen beim Beispielstatus auf: Er wurde zunächst ohne die Liste berechnet (alle 22 Beispiele „mit Hinweisen“); behoben, mit Test.

### Code-Review (eingebaute Prüfung `/code-review`, Stufe high, über `00f80ad..e7c8bae`)

9 Funde. Behoben in `3aa9219`:

1. Eigenschaftsbaum rief je Referenz bis zu dreimal den Index ab; jetzt nur noch das Ziel.
2. `references_among` mit bis zu 2000 Platzhaltern (ältere SQLite-Versionen: 999); jetzt in Stapeln zu 500, mit Test.
3. Diagnosen standen nicht nach Datei gruppiert; jetzt nach Datei sortiert, mit Test.
4. Unbekannter Referenzstatus in der Fahrtenliste konnte einen `KeyError` auslösen; jetzt Rückfall auf „nicht aufgelöst“.
5. Herkunftskette zeigte nach Klick auf eine Diagnose weiter die alte Auswahl; jetzt ausgeblendet, solange die Stelle einer Diagnose gezeigt wird, mit Test.
6. Eingehende Verweise ohne umschliessendes Objekt zeigten „erwartet: …“ statt der Quelle; jetzt das Ref-Element.

Nicht behoben, dem Benutzer vorgelegt ([open-points.md](open-points.md) Punkte 5–7):

- **Ref-Namen ausserhalb der Liste** (z. B. `DefaultCodespaceRef` aus den Guide-Vorlagen) erscheinen als „extern oder nicht geladen“, auch wenn das Ziel in der Datei steht. Die vom Review vorgeschlagene Abhilfe („ID unter anderem Typ vorhanden → Fehler“) habe ich ausprobiert und verworfen: Sie erzeugt Fehlalarme bei `Quay`/`ScheduledStopPoint` mit gleicher ID in `NETWORK_OFFER`-Dateien, dem zentralen Fall des Guides. Test mit Fixture ergänzt.
- **Abweichende Version** einer Referenz auf genau ein Objekt ist „aufgelöst“ ohne Hinweis (so entschieden, Frage offen).
- **Je Referenz eine Abfrage** beim Öffnen und alle Referenzen im Speicher: für kleine Dateien unkritisch, für grosse Lieferungen nicht geeignet (Variante B des Index).

### Sicherheits-Review (eingebaute Prüfung `/security-review`, über `00f80ad..3aa9219`)

**Keine Funde.** Geprüft: SQL (nur Platzhalter und feste Spaltennamen, alle Werte als Parameter), neuer Aufruf `GET /api/objects/{id}/provenance` (nur zufällige Datensatz-ID plus Elementnummer, kein Pfad), `config/ref-targets.json` (Grösse, JSON-Form und Namensmuster geprüft), keine neue XML-Verarbeitung (`DOCTYPE`-Abweisung gilt weiter), Frontend (Werte nur als Text, Farben nur aus validiertem `#RRGGBB`), keine Datenpreisgabe über den bereits geöffneten Datensatz hinaus. Die eingebaute Prüfung vergleicht mit `origin/HEAD`; das Repository hat kein Remote, deshalb wurde vorübergehend eine lokale Referenz auf `00f80ad` angelegt und danach gelöscht.

### Review durch Opus und Korrekturen (über `00f80ad..0e38a37`)

Funde und Entscheide des Benutzers (31.10.2026) sind in [decisions.md](decisions.md) „Entscheide nach Review Phase 2“ festgehalten. Korrekturen in den Commits `b782b13` (Entscheide) und `92a8738` (Frontend) sowie im Commit „Korrekturen aus dem Review Phase 2“ (Backend).

**Behoben:**

1. `config/ref-targets.json` war unvollständig (z. B. `JourneyPatternRef` ohne `DeadRunJourneyPattern`, `FromPointRef` nur `ScheduledStopPoint`). Jetzt nennt sie je Ref-Namen alle laut XSD erlaubten Zieltypen (47 Einträge, Feld `xsdTypes`). Der Test prüft jeden Eintrag gegen die XSD (alle erlaubten Typen vorhanden, nichts Zusätzliches) und deckt auch die Vorlagen `src/templates/*.xml` ab (Ref-Name in der Liste oder Zieltyp folgt eindeutig aus dem Namen).
2. Frontend: `useLoad` verwirft beim Schlüsselwechsel die alten Daten (kein Klick mehr auf die alte Herkunftskette); Vitest-Tests für `useLoad` und `ProvenanceChain`.
3. `ref_targets` ist Pflichtparameter (`open_dataset`, `DatasetIndex`, `inspect_guide`, `analyze_examples`); die Tests verwenden die echte Liste (`tests/support.py: REF_TARGETS`); der eine bewusste Test ohne Liste übergibt `{}` und sagt es im Kommentar.
4. Aufräumen: `resolve`/`ResolveResult` liegen jetzt am Index (`DatasetIndex.resolve`), `references.py` kennt den Index nicht mehr, kein `TYPE_CHECKING`-Zyklus; `objects_by_id` aus dem Index entfernt (Hilfsfunktion nur in den Tests); Sprachschlüssel `refs.owner` entfernt; `journeys.py` behandelt `RESOLVED` ohne Ziel als Programmfehler (`RuntimeError`, mit Test) und ersetzt unerwartete Status nicht mehr still; `_XML_NAME` mit `fullmatch` (Test mit `"Line\n"`).
5. Entscheid: abweichende Version einer Referenz ergibt ℹ Hinweis `reference.version_differs` (Referenz bleibt aufgelöst; Text de/en, Hilfeseite und `docs/api.md` nachgeführt).

**Offen** ([open-points.md](open-points.md)): Punkt 7 (viele Einzelabfragen pro Referenz in `object_detail`/`reference_view` und beim Auflösen; um `object_detail` ergänzt, nicht behoben), 8 (Punkt-in-Muster-Refs erlauben laut XSD jede Klasse), 9 (`ParentJourneyRef` → `ServiceJourney` in Beispiel 21, nicht in der XSD), 10 (zwei Vorlagen-Namen ohne XSD-Deklaration), 11 (Liste nur für Ref-Namen der Guide-Dateien, nicht für alle 403 der XSD).

**Nachweis:** `uv run python scripts/check.py` grün (alle Schritte). pytest: **351 Tests bestanden**; Abdeckung `app/core` **98 %**. Vitest: **69 Tests bestanden**. `scripts/test.py`: bestanden, 22 Beispiele laden (21 „ohne Meldungen“, Beispiel 17 „mit Hinweisen“); Referenzen der Beispiele unverändert: **1516 aufgelöst, 4 `external_or_unloaded`, 0 nicht auflösbar** (insgesamt 1520), keine neuen Versionshinweise.

### Lücken und Hinweise

- Herkunftskette zeigt in Phase 2 nur Frame, Objekte, Angabe und Ziel; Rechenketten berechneter Zeiten folgen mit Phase 3.
- Verweise ausserhalb des Datensatzes lösen sich erst, wenn die Gegendatei mit geöffnet wird; „Datei öffnen“ mit mehreren Dateien folgt in Phase 4. Im Beispiel 17 bleiben deshalb 4 Hinweise.
- Der Build meldet weiter ein Skriptpaket über 500 kB (CodeMirror).
- Windows: nicht getestet.
- Regel Z4 (welcher `TimingLink` gilt) ist entschieden und folgt mit Phase 3 ([mapping.md](mapping.md)).

## Phase 3: Fahrtansicht CH 2.0 (31.10.2026)

Umsetzung: Commits `6940210` (Kern), `c530cc9` (Schnittstelle), `0557561` (Oberfläche, Hilfeseite, README), `1ba5c25` (Entscheide, offene Punkte, Korrekturen) und der Commit mit diesem Bericht. Umgebung wie Phase 0. Guide `b7ac158`, XSD `73b337e`. Die Phase wurde von Claude ohne Rückfragen an den Benutzer umgesetzt; alle fachlichen Festlegungen und Fragen stehen in [decisions.md](decisions.md) („Umsetzung Phase 3“), [assumptions.md](assumptions.md) und [open-points.md](open-points.md) (Punkte 12–17).

### Prüfbefehl

`uv run python scripts/check.py --hook`: **grün** bei allen vier Commits (Git-Hook). Alle 14 Schritte OK, pip-audit und npm audit ohne Lücken. `uv run python scripts/test.py`: bestanden, `guide-tested.json` unverändert (22 Beispiele, Ergebnisse wie in Phase 2).

### Tests und Abdeckung

- pytest: **505 Tests bestanden**, davon 43 in `tests/guide` gegen den Guide-Klon (alle 22 Beispiele einzeln geladen **und** die Fahrtansicht jeder Fahrt gebaut: 42 Fahrten, 338 Zeiten, 17 davon „nicht berechenbar“ wegen Lücken in den Daten (Beispiele 04, 07, 11); fachliche Tests an 01, 08, 15, 21). Abdeckung `app/core`: **98,2 %** (`app/core/projection/`: `timing.py` 99 %, `journey_view.py` 99 %, `notices.py` 98 %, `offers.py` 97 %, `calendar.py`, `clock.py`, `master_data.py` 100 %, `common.py` 88 %).
- Vitest: **115 Tests bestanden** (u. a. Fahrtansicht im App-Ablauf, Rechenkette mit Standardwerten und Grund, Umschalten Fahrt/Objekt im Verlauf, Zeit- und Datumsformat, Stammdaten, Betriebstage in Deutsch und Englisch, Halte ohne Haltestelle, Hinweise mit Strecke).
- Synthetische Fixtures: `ch20_three_stops`, `ch20_midnight`, `ch20_missing_runtime`, `ch20_network_offer` (+ `ch20_site_offer`) und neu `ch20_offers.xml` (XSD-gültig); dazu ein Szenario-Baukasten (`tests/core/projection/builders.py`) für Randfälle der Zeitberechnung.

### Abnahme

| Kriterium | Ergebnis |
|---|---|
| Beispiel 01: Halte in richtiger Reihenfolge, nachvollziehbar berechnete Zeiten mit Rechenkette | erfüllt: Spiez ab 10:35, Interlaken West an 10:45 / ab 10:48, Interlaken Ost an 10:54; Rechenkette `DepartureTime` 10:35 + `DepartureDayOffset` 0 + `RunTime` PT10M (`tl-1`) + `WaitTime` PT3M + `RunTime` PT6M (`tl-2`), jeder Summand mit eigenem Quellelement, anklickbar (Test `test_example_01_stops_and_calculated_times`, im Browser geprüft: Klick auf den Summanden markiert genau `<RunTime>PT6M</RunTime>`) |
| Abweichung zum Dateikommentar 10:53/10:54 geklärt und in `docs/assumptions.md` festgehalten | erfüllt: der Kommentar nennt 10:53, die Daten ergeben 10:54; keine weiteren Summanden; Fehler im Beispiel, nicht im Tool ([assumptions.md](assumptions.md) Abschnitt 1, Test hält den Kommentar fest) |
| Beispiel 15 (`DepartureDayOffset` 1) korrekt | erfüllt: Abfahrt 04:34 +1, Zwischenhalte 04:36 +1 / 04:37 +1 / 04:39 +1, Ankunft 04:41 +1; Tag „ausdrücklich“ (Quelle `DepartureDayOffset`) |
| Beispiel 21 (Kurswagen über Mitternacht) korrekt | erfüllt: Kurswagen `KW37` Zürich HB ab 22:15, Basel Bad Bf an 23:19 / ab 23:40, Hannover Hbf an 06:12 +1 / ab 06:44 +1 (Tageswechsel „berechnet“), Bremen Hbf an 07:54 +1; die ausdrücklichen Zeiten der drei Teilstrecken (mit `…TimeDayOffset`) bestätigen die Rechnung. Hinweise zur Zeitumstellung (29.03. und 25.10.2026). Betriebstage: alle vier Fahrten haben dieselbe `AvailabilityCondition` (365 von 365 Tagen); die Prüfung gegen die Elternfahrt ist nicht umgesetzt (offener Punkt 14) |
| Beispiel 08 zeigt Angebote auf Teilstrecken | erfüllt: Bistro (`bistro` = Angebot `WS`, Mappingtabelle Blatt `Angebote` Zeile 103) bei den Halten Bern–Olten und Zürich HB–St. Gallen, für die ganze Fahrt 1. Klasse (`firstClass`, Zeile 115) und `freeWifi` (keine Erläuterung); Teilstrecken-Zeiten stimmen mit den berechneten überein; Hinweise mit Strecke (Halt 1–2, 3–5) |
| Alle übrigen Inhalte des Plans (Kopf, Betriebstage mit aufklappbarer Liste, `order`-Hinweis, Standardwerte, Zeitumstellung, Hinweise in allen Sprachen) | erfüllt, siehe Tests; Browser (Chrome, Playwright aus dem Scratchpad) für die Beispiele 01, 08, 15 und 21: Halt anklicken → richtige XML-Stelle (`<Name lang="de">Interlaken West</Name>`), Frame `ServiceFrame`; Sprache Englisch; **Browser-Konsole leer** |
| Hilfeseite nachgeführt | erfüllt: sieben Funktionen (Fahrtansicht, Berechnete Zeiten, Tageswechsel/Zeitumstellung, Betriebstage, Angebote/Teilstrecken, Hinweise, Stammdaten) und der Prüfschritt „Plausibilität der Fahrtansicht“ in beiden Sprachdateien; Meldungsschlüssel (`projection.*`) übersetzt; README nachgeführt; Test `tests/test_help_texts.py` |

### Wichtigste Befunde der Phase

1. **`ValidDayBits` passt in 15 von 22 Beispielen nicht zum Zeitraum** (373 statt 365 Bits, zu kurze oder sehr kurze Folgen). Das Tool zeigt dann keine Tage, nur die Anzahl gesetzter Bits, mit △ Warnung ([assumptions.md](assumptions.md) Abschnitt 3).
2. **Widerspruch im Guide zu Teilstrecken:** `uc05` („überschreibt“) gegen Beispiel 08 (ergänzt); `uc08` („kein `JourneyPart` für Kurswagen“) gegen Beispiel 21. Beide Fälle als offene Punkte vorgelegt (12) bzw. in den Annahmen festgehalten.
3. Nur 4 von 22 Beispielen nennen den `OnwardTimingLinkRef`; für die übrigen bestimmt die vom Benutzer festgelegte Regel Z4 den `TimingLink` über Von-/Nach-Punkt (ℹ Hinweis).
4. Beispiel 04 (`RunTime` `P3M`), 07 und 11 haben Lücken, die Zeiten „nicht berechenbar“ machen; sie bleiben sichtbar (Grund mit Stelle).

### Selbstkontrolle (Code-Review und Sicherheits-Review über `95cfdd8..1ba5c25`)

Eigene Durchsicht der Commits gegen die Regeln aus `CLAUDE.md` und `docs/engineering-guidelines.md` (Korrektheit, nichts erfinden, Herkunft, Texte in Sprachdateien, keine Ausnahmen von Prüfregeln, Schichten). Funde, alle behoben:

1. Eine Teilstrecke mit genanntem, aber nicht zuordenbarem Ende deckte den Anfangshalt allein ab (geraten): jetzt deckt sie keinen Halt ab und ist als „nicht zugeordnet“ gekennzeichnet; Test ergänzt.
2. `StopView.part_numbers` war eine veränderliche Liste in einer unveränderlichen Klasse und wurde nachträglich gefüllt: jetzt vor dem Bau der Halte berechnet (Tupel).
3. Der Vermerk „TimingLink über Von-/Nach-Punkt bestimmt“ gründete auf einer Liste über die ganze Fahrt statt auf der einzelnen Strecke (Falschkennzeichnung möglich): jetzt je Strecke bestimmt, Test ergänzt.
4. Die Nummer des Halts im Grund „Fahrplanpunkt nicht auflösbar“ war um eins falsch; Test angepasst.
5. `NoticeAssignment` in einem `StopPointInJourneyPattern` (Guide `06_service.md` Z. 105) fehlte; ergänzt (Geltungsbereich „Halt“).
6. Stammdaten füllten die Oberfläche (alle Spalten je Zeile); jetzt zusammengefasst und aufklappbar. Die rechte Spalte (Rechenkette, Herkunft, XML) bleibt beim Scrollen sichtbar, die Mitte ist breiter.

Sicherheit: keine Funde. Der neue Aufruf nimmt nur eine zufällige Datensatz-ID mit Elementnummer (Format geprüft, unbekannte IDs und Nicht-Fahrten ergeben 404), kein Pfad, kein neues SQL (nur bestehende Abfragen des Index), keine neue XML-Verarbeitung. Werte aus Dateien erscheinen im Frontend nur als Text oder Attribut-Text (kein `innerHTML`), Farben stammen aus der geprüften Konfiguration, die CSP blieb unverändert (Browser-Konsole ohne Verstösse).

### Review durch Opus und Korrekturen (über `95cfdd8..3a558ae`)

Acht Funde des Reviews, alle behoben; der Entscheid zu den Phase-3-Festlegungen bleibt beim Benutzer ([decisions.md](decisions.md) unverändert).

1. `_assignments`: die `PassengerStopAssignment` wurde nur unter den ersten 100 eingehenden Verweisen gesucht. Jetzt gezielte Abfrage `DatasetIndex.referencing_parents` ohne Obergrenze; Test mit 150 weiteren Verweisen auf den Fahrplanpunkt.
2. Hinweiszuweisung ohne `EndPointInPatternRef`: Ende = Anfang (XSD „If absent same as Start Point“, Regel N2a in [mapping.md](mapping.md)); Beispiel 10 (`ch:1:NoticeAssignment:1`) zeigt „bei Halt n“ statt „nennt Halte, die nicht zu dieser Fahrt gehören“. Test.
3. `_referencing` (Hinweise): kein Abschneiden bei 500 Verweisen mehr (gleiche Abfrage wie 1); Test mit 520 Zuweisungen.
4. `JourneyWaitTime` ohne `WaitTime`: Abfahrt „nicht berechenbar“ mit Grund `projection.time.wait_time_missing` (Z5b, de/en); Standardwert 0 nur ohne passende `JourneyWaitTime`. Test angepasst.
5. Frontend: Knopf im Knopf in `OperatingDays`, `JourneyView` (Kategorie) und `Facilities`; neuer Baustein `ReasonText` erzeugt immer genau einen Knopf. Vitest: kein `button button` in diesen Bausteinen, ein Klick löst genau eine Auswahl aus.
6. Mehrere passende `TimingLink` ohne `RunTime`: „mehrdeutig“ statt „nicht gefunden“ (Text von `timing_link_ambiguous` entsprechend allgemeiner, de/en). Test.
7. Leistung: `TimingLink` über gezielte Abfrage (Von-Punkt) statt alle je Anfrage; `unassigned_count` einmal je Datensatz (`DatasetIndex.cached`); Test auf `StopPlace` als `LIMIT 1` (`has_object_type`). Keine Verhaltensänderung ausser: Verweise, die nicht aufgelöst sind und dieselbe `id` nennen, zählen jetzt auch bei Zuordnung und Hinweisen (wie schon bei den `TimingLink`).
8. Doppelter Code: `_matches`/`_ref_target` durch `common.points_to` ersetzt; `_assignments` und `_referencing` nutzen dieselbe Abfrage `referencing_parents`.

**Abnahmewerte** (Zusammenfassung über alle 22 Beispiele vor und nach den Korrekturen verglichen: Fahrten, Zeiten, Zeitwerte, Hinweise samt Halteposition, Haltestellen und Quais): Beispiele 01, 08, 15, 21 unverändert; „nicht berechenbar“ unverändert 17 von 338 Zeiten (Beispiele 04, 07, 11; Grund: Lücken in den Daten). Einzige Änderung: Beispiel 10 (Hinweis `ch:1:NoticeAssignment:1`, Fund 2).

**Nachweis:** `uv run python scripts/check.py` grün (alle Schritte). pytest: **513 Tests bestanden**; Abdeckung `app/core` **99 %**. Vitest: **117 Tests bestanden**. `scripts/test.py`: bestanden, `guide-tested.json` unverändert.

### Lücken und Hinweise

- Offen und dem Benutzer vorgelegt: [open-points.md](open-points.md) 12–17 (Angebote Teilstrecke gegen Fahrt, Hinweiszuweisungen ohne Ziel, Betriebstage-Prüfung der Kurswagen, zu bestätigende Annahmen, Befunde und Beispielstatus, nicht dargestellte Inhalte).
- Nicht dargestellt: Zieländerung (`DestinationDisplay`), Takt, Formation, Flügelung, Durchbindung, Bedarfsverkehr, Elternfahrt der Kurswagen (im Objekt-Explorer sichtbar).
- Die Fahrtansicht baut sich bei jedem Abruf neu auf (je Halt mehrere Abfragen an den Index) und begrenzt die Zahl der Halte nicht; für die Guide-Beispiele (grösste Fahrt 64 Halte) unkritisch, für grosse Lieferungen später anzupassen (offener Punkt 7).
- Die Zeitumstellung wird nur für Betriebstage mit auflistbaren `ValidDayBits` geprüft (bei 15 von 22 Beispielen weicht deren Länge ab).
- Der Build meldet weiter ein Skriptpaket über 500 kB (CodeMirror). Windows: nicht getestet.

## Phase 4: Eigene Dateien und Validierung (31.10.2026)

Umgesetzt in `980fcd6` (Entscheide) und `032e2ee` (Umsetzung) sowie dem Abschluss-Commit mit diesem Bericht. Abweichungen vom Plan und technische Festlegungen: [decisions.md](decisions.md) „Umsetzung Phase 4“.

### Prüfbefehl

`uv run python scripts/check.py` grün (Lockfile, ruff, ruff format, mypy --strict, pytest mit Abdeckung, npm ci, TypeScript, Biome, Vitest, Build, pip-audit, npm audit, Git-Hook). `uv run python scripts/test.py` bestanden; `guide-tested.json` neu geschrieben (Guide `b7ac158`, XSD `73b337e`, 22 Beispiele: 12 ohne Meldungen, 1 mit Hinweisen (17), 9 mit Fehlern (`order`)). Neue Abhängigkeiten: `lxml` 6.1.3 (geplant), `python-multipart` 0.0.33 (FastAPI-Formulare).

### Tests und Abdeckung

- pytest: **763 Tests bestanden** (vorher 513), Abdeckung `app/core` **98,4 %** (Mindestwert 90 %); neue Module: `intake.py` 95 %, `validation/*` und `guide/links.py` 96–100 %.
- Vitest: **147 Tests bestanden** (vorher 119).
- Neue Testdateien: `tests/core/test_intake.py` (Namen, ZIP, Grenzwerte, Arbeitsverzeichnis), `tests/core/validation/` (`test_detection.py`, `test_core_rules.py` mit je einem verletzenden und einhaltenden Fall zu jeder der 30 Regeln aus den Regeldaten, `test_lxml_checks.py`, `test_engine.py` mit echter XSD), `tests/core/guide/test_links.py`, `tests/core/test_dataset.py`, `tests/server/test_upload_api.py`, `tests/server/test_runtime.py`; Frontend: `OpenFiles`, `DatasetPanel`, `DiagnosticList`, App-Abläufe (Öffnen, Prüfen, Schliessen, Nachfragen während des Ladens), `api.test.ts`.
- Die echte XSD (rund 17 s) wird einmal je Testlauf geladen (Fixture `guide_engine`); ohne Guide-Klon werden diese Tests übersprungen, unter `scripts/test.py` schlagen sie fehl.

### Abnahme

| Kriterium | Ergebnis |
|---|---|
| Eigene 2.0-Datei wird geprüft: `fixtures/ch20_three_stops.xml` hochladen, XSD gültig, keine Kernregel-Verstösse | erfüllt: Browser (Chrome, Playwright, `setInputFiles` am Dialog „Datei öffnen“): erkannt als „CH-Profil 2.0 (Entwurf)“ mit drei Begründungen; „Prüfen“: „Geprüft gegen Entwurf b7ac158“, drei Schritte durchgeführt, „keine Diagnosen“. Test `test_three_stops_is_valid_and_has_no_core_rule_violation`. Dazu wurde die Fixture um eine `TypeOfProductCategory` ergänzt (Kernregel CH-SJ-07). |
| 1.10-Datei (`fixtures/netex110_like.xml`) wird erkannt und nicht irreführend geprüft | erfüllt: „Erkannt: NeTEx 1.10“ (Begründung: `version="1.10"`, `schemaLocation` 1.10, Kommentar `Profile: SBBSplitted`, `calls`); „Prüfen“ gesperrt, Hinweis „Keine Datei ist als CH 2.0 erkannt“; über die Schnittstelle: Datei „nicht geprüft“ mit Grund, keine Diagnosen der Arten `xsd`/`profile_rule`; Objekt-Explorer und Fahrten bleiben nutzbar. Alle 22 Guide-Beispiele (auch 01 und 20 mit `version="1.09"`, 08 ohne Attribut) werden als CH 2.0 erkannt (Test `test_every_guide_example_is_ch20`). |
| `order`-Verstösse der Beispiele mit Stelle und Link zum Guide-Kapitel | erfüllt: 121 Verstösse (Beispiel 22: 66) mit Zeile und Spalte (Klick markiert die Stelle im XML); Link `…/blob/b7ac15860369818a8fb53c64ed6f71318f019380/src/03_xml_modelling.md` (Kapitel zu Versionen und Reihenfolge). Abweichung: **9** Beispiele, nicht 11 ([open-points.md](open-points.md) 18). Alle 22 Beispiele sind XSD-gültig (Test). |
| `fixtures/ch20_calls.xml` verletzt die Kernregel (calls verboten) mit Quellenangabe | erfüllt: `CH-SJ-13: ServiceJourney ch:1:sjyid:SYN:1 darf calls nicht enthalten (Quelle: templates/ServiceJourney.xml Z. 145-153)`, ⚠ Fehler, Stelle Zeile 164, Link auf `08_timetable.md` im geprüften Commit; dazu CH-SJ-07 (Fixture hat keine Produktkategorie). |
| `fixtures/ch20_duplicate_id.xml` ergibt XSD-Fehler | erfüllt: Art „XSD“, `Duplicate key-sequence ['ch:1:sloid:SYN2:0:1', '1'] in key identity-constraint …` (Originalwortlaut), Zeile 61; getrennt von Art „Referenz“ (mehrdeutig). |
| Sicherheitstests: XXE/DOCTYPE | erfüllt: `security_xxe.xml` wird vom Einleser abgewiesen (`xml.doctype_forbidden`), lxml sieht die Datei nie; „Prüfen“ stürzt nicht ab; der Inhalt von `xxe_secret.txt` erscheint in keiner Antwort (Test `test_xxe_and_doctype_are_rejected_without_leaking`); `parse_safely` weist DOCTYPE zusätzlich ab (offener Punkt 4 erledigt). |
| Zip-Slip | erfüllt: `../x.xml`, `a/../../x.xml`, `/abs/x.xml`, `\x.xml`, `C:/x.xml`, zu tiefe Pfade werden abgewiesen (`zip.unsafe_path`), nichts ausserhalb von `work/` entsteht (Tests in `test_intake.py`, `test_upload_api.py`; Browser: `evil.zip`). |
| ZIP-Grenzwerte (Gesamt, Einzeldatei, Anzahl, Kompressionsrate) | erfüllt: je ein Test mit kleinen Grenzwerten über `receive` und über die Schnittstelle; zusätzlich Abbruch beim Entpacken, wenn ein Eintrag oder alle zusammen mehr Bytes liefern als der Kopf angibt. |
| Symlink im ZIP, unzulässige Dateinamen | erfüllt: `zip.symlink`; Namen mit `..`, Ordnerteilen, `\`, Steuerzeichen, Gerätenamen (`CON`) werden bereinigt und gemeldet (`file.name_changed`). |
| HTML in XML-Werten | erfüllt: Der Wert erscheint als Text (Schnittstelle liefert JSON mit `nosniff`; Browser: `<img onerror>`/`<script>` im `Name` laufen nicht, `window.__xss` bleibt unbelegt, keine Dialoge); Vitest: Diagnosen-Text ohne HTML-Element, nur `https`-Links. |
| Zu grosser Upload | erfüllt: 413 `error.payload_too_large` vor dem Lesen des Rumpfs (zu grosse `Content-Length`, ohne `Content-Length`, zu viele Dateien); einzelne zu grosse Datei als Diagnose `file.too_large`. |
| ZIP-Testdateien zur Laufzeit erzeugt | erfüllt: alle ZIP-Dateien entstehen in den Tests aus den Fixtures (`*.zip` bleibt ausgeschlossen). |
| Aufräumen von `work/` | erfüllt: `DELETE /api/datasets/{id}`, Herausfallen aus den 10 offenen Datensätzen, Start (nur Ordner mit unseren Namen, keine Links verfolgt); Tests. |
| Beispielstatus mit den neuen Prüfungen; `scripts/test.py` schreibt sie | erfüllt: XML-Syntax, XSD, `general_rules.sch`, Kernregeln, Referenzen; Befunde der Fahrtansicht zählen nicht ([decisions.md](decisions.md) „Kernregeln Phase 4“ (6)). Die Beispiele werden im Hintergrund geprüft; die Guide-Status-Box zeigt „XSD wird geladen …“, dann „Beispiele werden geprüft …“, dann „bereit“ (Browser, Vitest). |
| Hilfeseite, Sprachdateien, README nachgeführt | erfüllt: drei Funktionen (Datei öffnen, Versionserkennung, Prüfen), die Schritte `xsd`, `general_rules`, `ch_core_rules` als „durchgeführt“, Abschnitt „Schweizer Kernregeln für den Fahrplan“ (30 Regeln aus den Daten, mit Quelle) in `de-CH.json` und `en.json`; Test `tests/test_help_texts.py`. |
| Browser-Konsole | leer (Playwright, alle Abläufe: Öffnen, Prüfen, 1.10, ZIP, böse ZIP, XXE, XSS, Hilfeseite). |

### Wichtigste Befunde der Phase

1. Die Messung der `order`-Verstösse bestätigt 121 und Beispiel 22 mit 66, aber in **9 statt 11** Beispielen.
2. Alle 22 Guide-Beispiele sind XSD-gültig; mit den Kernregeln gibt es nur 3 Hinweise „Rumpf-Fahrt“ (Beispiel 17) und 3 △ Warnungen CH-JP-01 (Beispiel 21, `DirectCarriage`).
3. Der Index `A5_annex_index.md` kennt nicht jedes Element (z. B. `StopPointInJourneyPattern`) und nennt für `ServiceJourney` als erstes Kapitel `02_files`; deshalb nennen Kernregeln und Schematron-Regeln ihr Kapitel selbst, der Index dient für XSD-Befunde ([open-points.md](open-points.md) 20).
4. Mit den Kernregeln verletzen die meisten `ch20_*`-Fixtures CH-SJ-07 (keine Produktkategorie); nur `ch20_three_stops.xml` wurde ergänzt ([open-points.md](open-points.md) 21).

### Selbstkontrolle (Code-Review und Sicherheits-Review über `980fcd6..032e2ee`)

Eigene Durchsicht gegen `CLAUDE.md` und `docs/engineering-guidelines.md`; Funde, alle behoben:

1. **ZIP-Beiwerk:** `._x.xml` wurde am bereinigten Namen geprüft (der führende Punkt war schon entfernt) und als Fahrplan gelesen; jetzt wird der rohe Eintragsname geprüft (Test `test_zip_skips_os_noise` fand es).
2. **Totes Stück Code:** Die Gesamtgrenze nach dem Schreiben eines Eintrags konnte nie anschlagen (die Schreibgrenze war schon der Rest); ersetzt durch `_TotalExceededError` mit eigener Meldung `zip.total_too_large` (Test mit lügenden Kopfzeilen).
3. **Link zum Guide-Kapitel:** Für `order`-Verstösse fehlte der Link (Element nicht im Index), für Kernregeln wäre das erste Kapitel unpassend gewesen: Regeln nennen ihr Kapitel (`chapter`), XSD-Befunde nutzen den Index; der Server prüft den Kapitelpfad (`^src/[A-Za-z0-9_]+\.md$`), das Frontend zeigt nur `https`-Links.
4. **Archiv als „nicht lesbar“:** Ein ZIP mit nur Hinweisen erschien in der Dateiliste als „✖ nicht lesbar“; jetzt „keine XML-Datei (siehe Diagnosen)“.
5. **Überholte Öffnung:** Antwortet eine ältere Öffnung nach einer neueren, schliesst die Oberfläche den überholten Datensatz auf dem Server (sonst Rest in `work/` bis zum Herausfallen).
6. **Typen:** `lxml-stubs` sind unvollständig; lxml gilt als untypisiert (mit Begründung in `pyproject.toml` und `decisions.md`), die Aufrufer sind typisiert (`ParsedDocument`). Keine `noqa`/`type: ignore`/`biome-ignore` im Code.
7. **Fixture:** Die Abnahme „keine Kernregel-Verstösse“ verlangte eine Produktkategorie in `ch20_three_stops.xml`; Tests der Fahrtansicht angepasst (eine Kategorie statt keiner).

Sicherheit (Upload, ZIP, lxml, Pfade, IDs, XSS) geprüft, keine offenen Funde: Dateinamen bereinigt (kein Ordnerteil, `:` und Steuerzeichen ersetzt, Gerätenamen, Länge); ZIP-Einträge einzeln geprüft (Pfad, Symlink, Rate, Grösse) und mit exklusivem Anlegen (`xb`) in einen frischen Ordner mit zufälligem Namen geschrieben, `resolve()` und `is_relative_to` als zweite Sperre; Entpacken mit Obergrenze unabhängig von den Kopfzeilen; Aufräumen folgt keinen Links; Upload nur mit `Content-Length`; die API nimmt keine Pfade; IDs vom bekannten Format; lxml nur mit gehärtetem Parser, DOCTYPE doppelt abgewiesen, ohne Netzzugriff, ohne `huge_tree`; Werte aus Dateien nur als Text; Links nur `https` mit geprüftem Kapitelpfad und geprüftem Commit.

### Lücken und Hinweise

- Offene Punkte 18–21 sind vom Benutzer am 31.10.2026 entschieden (siehe unten „Bestätigungen und Knopf“); nichts offen.
- Nicht umgesetzt (Entscheide vom 31.10.2026): CH-SJP-08, CH-SJ-16. Nicht eingebunden: übrige ~330 Profilregeln, Erklärungen und Korrekturvorschläge der XSD-Meldungen (Originalwortlaut).
- Ein Upload liegt beim Annehmen bis zu 200 MB im Arbeitsspeicher (Rohdaten, danach nur noch Index und Text); nach der Korrektur zum Review wird nichts mehr zurückgelesen oder im Datensatz behalten. Streaming in `work/` bleibt für grosse Lieferungen zurückgestellt.
- Eine Validierung vor Ende des XSD-Ladens wartet bis zu 17 s.
- Die Prüfung der Beispiele im Hintergrund schlägt ohne XSD (Submodul nicht geholt) nicht fehl: der Schritt `xsd` ist dann „nicht durchgeführt“.
- Die Tests lassen einige SQLite-Datensätze ungeschlossen (`ResourceWarning`, harmlos). Windows: nicht getestet.

### Review durch Opus und Korrekturen (Stand der Korrekturen: 31.10.2026)

Code-Review (Opus) über `2c6a3e1..96ec455`, Funde 1 bis 10; dazu die Härtung 11 aus dem Sicherheits-Review. Alle behoben; technische Festlegungen: [decisions.md](decisions.md) „Korrekturen nach Review Phase 4“, Schnittstelle: [api.md](api.md).

| Nr. | Fund | Behebung | Test |
|---|---|---|---|
| 1 | `remove` schloss den Index sofort; eine laufende Anfrage (z. B. Validierung) endete mit 500 | `Dataset.acquire`/`release`/`close` mit Zähler: Schliessen und Verdrängen wirken nach der letzten Anfrage; die Schnittstelle hält den Datensatz je Anfrage fest (Abhängigkeiten mit `yield`). Oberfläche: Ergebnis, Fehler und „läuft“ einer Prüfung nur für den Datensatz, für den sie gestartet wurde | `test_closing_during_a_validation_does_not_break_it`, `test_close_waits_for_running_requests`, `test_registry_evicts_oldest`; Vitest (zwei Tests zu später geöffnetem Datensatz) |
| 2 | `maxTotalBytes` galt je ZIP statt je Upload | gemeinsames Budget für alle XML-Dateien und ZIP-Archive eines Uploads, neue Meldung `file.total_too_large` | drei Tests in `test_intake.py`, ein API-Test |
| 3 | `FILE_NAME_CHANGED` am bereinigten Namen, ehe `_unique` ihn änderte (falsche Datei); keine Meldung bei reiner `_unique`-Umbenennung | Meldung am endgültigen Namen, auch bei `_unique` und bei ZIP-Einträgen | `test_unique_rename_is_reported_at_the_final_name`, `test_cleaned_name_taken_by_an_earlier_file_does_not_overwrite_it`, ZIP-Namenstest |
| 4 | Eine Ausnahme bei einem Beispiel brach `complete_examples` ab, `examples_ready` blieb falsch, die Oberfläche fragte endlos | Fehler von lxml, SQLite und Dateizugriff je Beispiel: Ergebnis `check_failed` („Prüfung fehlgeschlagen“), protokolliert; Programmfehler brechen weiter ab, doch `Runtime.complete_examples` setzt am Ende immer `examples_ready` (offene Beispiele = `check_failed`); Oberfläche: Nachfragen endet erst nach 5 Fehlschlägen in Folge | vier Tests in `test_status.py`, `test_runtime.py`; zwei Vitest-Tests, ein Vitest-Test zur Anzeige |
| 5 | `DiagnosticList` lud bei erneutem „Prüfen“ nicht neu | Schlüssel zählt die abgeschlossenen Validierungen | Vitest `lädt die Diagnosen bei jeder erneuten Prüfung neu` |
| 6 | Gerätenamen `COM¹`/`LPT²` und `CON .xml` wurden nicht erkannt | Vergleich nach Entfernen von Leerzeichen und Punkten am Ende des Basisnamens, `¹²³` wie `123` | sieben neue Fälle in `test_clean_name` |
| 7 | XSD und `general_rules` galten als „durchgeführt“, auch ohne prüfbare Datei | „durchgeführt“ nur, wenn mindestens eine Datei geprüft wurde; sonst `validation.step_no_file` (de/en). Gleiches für `ch_core_rules` | vier Tests in `test_engine.py` |
| 8 | Leistung: je Befund ein Commit, je Element eine Abfrage der Kinder | Befunde je Datei gebündelt (ein `add_diagnostics`), `DatasetIndex.children_of` lädt Kinder gesammelt; Verhalten unverändert | `test_findings_of_a_file_are_added_with_one_call`, `test_children_of_many_elements_matches_single_queries`; bestehende Kernregel-Tests |
| 9 | Doppelte Datenklasse `IntakeNote`/`FileNote` | eine Klasse `FileNote` in `app/core/dataset.py`, das Umkopieren in `dataset_routes.py` entfällt | bestehende Tests angepasst |
| 10 | Speicher: `Dataset.file_data` hielt alle Rohdaten; beim Upload mehrfach im Speicher | `SourceFile.path`; `Dataset.read_file` liest aus `work/` bzw. dem Guide-Klon; kein Zurücklesen nach dem Speichern | `test_raw_data_is_read_from_the_file_not_kept_in_memory` |
| 11 | Härtung (Sicherheits-Review, kein Fund): Schutz vor Anfragen fremder Webseiten | Origin-Prüfung für POST/DELETE (Fehlt oder `http://127.0.0.1:<Port>`/`http://localhost:<Port>`), sonst 403 `error.forbidden_origin`; Vite-Proxy setzt den Origin im Entwicklungsmodus | `test_own_origin_may_change_state`, `test_foreign_origin_is_rejected_for_changes` (8 Origins), `test_foreign_origin_cannot_close_or_validate`, `test_requests_without_origin_are_accepted` |

Ergebnis des Sicherheits-Reviews (Opus): **keine Funde**; die Origin-Prüfung ist eine zusätzliche Härtung.

Offen: nichts aus diesem Review. Hinweise: Die Rohdaten eines Beispiels werden bei der Validierung neu aus dem Guide-Klon gelesen; ändert ein `git pull` die Datei bei geöffnetem Datensatz, stimmen Stellen der Befunde nicht mehr mit dem Index überein (Server neu starten, siehe [api.md](api.md) „Guide-Status“). Windows: weiterhin nicht getestet.

Prüfbefehl: `uv run python scripts/check.py` grün (alle Schritte wie oben); `uv run python scripts/test.py` bestanden, `guide-tested.json` unverändert (Guide `b7ac158`, XSD `73b337e`, 22 Beispiele).

Testzahlen nach den Korrekturen: pytest **805 Tests bestanden** (vorher 763), Abdeckung `app/core` **98 %** (Mindestwert 90 %; `intake.py` 96 %, `validation/engine.py` 97 %, `guide/status.py` 98 %); Vitest **152 Tests bestanden** (vorher 147).

### Bestätigungen und Knopf „Trotzdem als CH 2.0 prüfen“ (31.10.2026)

- **Bestätigt** vom Benutzer: die technischen Festlegungen „Umsetzung Phase 4“ und „Korrekturen nach Review Phase 4“ (inklusive: `ch_core_rules` ist „nicht durchgeführt“, wenn keine Datei prüfbar war). **Entschieden** (siehe [decisions.md](decisions.md) „Offene Punkte 18–21 aus Phase 4“): 18 berichtigt auf 9 Beispiele (Entscheid, Plan Abschnitt 8, `docs/research/guide-2.0.md`, `docs/mapping.md`); 20 und 21 bleiben wie umgesetzt.
- **Umgesetzt (Punkt 19):** `POST /api/datasets/{id}/validate?forceCh20=true` prüft auch lesbare Dateien mit Versionserkennung „mehrdeutig“ oder „unbekannt“ wie CH 2.0; erkannte andere Versionen (1.10) und nicht lesbare Dateien bleiben gesperrt. Das Ergebnis trägt `forced` (je Datei und im Ganzen; Meldung `validation.forced`), die Oberfläche zeigt „Als CH 2.0 geprüft auf Wunsch, Version nicht erkannt.“; zweiter Knopf „Trotzdem als CH 2.0 prüfen“ nur bei mehrdeutigen oder unbekannten lesbaren Dateien. Hilfeseite (de/en), README und [api.md](api.md) nachgeführt.
- **Tests:** neue Tests für Kern (Erkennung `forceable`, Engine: Standard prüft nicht, auf Wunsch geprüft und vermerkt, 1.10 und nicht lesbare Datei gesperrt, Wiederholung ersetzt), Schnittstelle (mit/ohne Parameter, 1.10, ungültiger Wert 422) und Vitest (Knopf bei ambiguous/unknown, nicht bei 1.10/unlesbar, gesperrt während der Prüfung, Vermerk im Ergebnis, Parameter im Aufruf). pytest **815 Tests bestanden** (vorher 805), Abdeckung `app/core` **98 %**; Vitest **157 Tests bestanden** (vorher 152). `uv run python scripts/check.py` grün, `uv run python scripts/test.py` bestanden (`guide-tested.json` unverändert).
- **Browser (Playwright, Chrome):** synthetische XML-Datei ohne Versionshinweise hochgeladen: „Version unbekannt“, „Prüfen“ gesperrt, „Trotzdem als CH 2.0 prüfen“ prüft; Ergebnis mit Vermerk, XSD- und Schematron-Befunde mit Stelle; Konsole leer; Server danach beendet.

## Phase 5: Übergabe (31.10.2026)

Umgesetzt in `5fa264f` (Korrektur der Origin-Prüfung, Test der Hilfeseiten-Daten) und `7bd8f2b` (E2E-Test, Sprachdatei-Prüfung, Hilfeseite, README) sowie dem Abschluss-Commit mit diesem Bericht. Technische Festlegungen (Claude, zur Bestätigung): [decisions.md](decisions.md) „Umsetzung Phase 5“.

### Prüfbefehl

`uv run python scripts/check.py` grün (alle 13 Schritte wie in Phase 4; als Git-Hook bei beiden Commits). `uv run python scripts/test.py` bestanden; `guide-tested.json` unverändert (Guide `b7ac158`, XSD `73b337e`, 22 Beispiele). Neue Abhängigkeit (Entwicklung): `@playwright/test` 1.64.1; `npm audit` meldet keine Funde.

### Tests und Abdeckung

- pytest: **820 Tests bestanden**, keine übersprungen (vorher 815); Abdeckung `app/core` **98 %** (Mindestwert 90 %).
- Vitest: **161 Tests bestanden** (vorher 152).
- E2E (Playwright): **1 Test bestanden** (`npm run e2e`, rund 4 s Testlauf nach dem Serverstart): einmal mit dem installierten Chrome (`E2E_BROWSER_CHANNEL=chrome`), einmal mit dem von Playwright installierten Chromium (`npm run e2e:install`, Standard), einmal in einem frischen Klon des Repositorys (siehe unten). Ohne Guide-Klon wird der Test übersprungen („1 skipped“), mit `NETEX_REQUIRE_GUIDE=1` schlägt er fehl (beides geprüft mit einem absichtlich falschen `guidePath`). Nach jedem Lauf ist der Server beendet und `work/` leer.
- Neue Tests: `tests/test_help_texts.py` (ungenutzte Schlüssel, Muster zusammengesetzter Schlüssel), `tests/server/test_api.py` (Hilfeseiten-Daten gegen `config/` und Liste der Prüfschritte; Origin-Prüfung mit abweichendem Port), Vitest `HelpPage.test.tsx` (Farben, Grau-Liste und Prüfungen genau aus den Daten, Quellen, Stand, Guide-Stand), `app/frontend/e2e/example01.spec.ts`.

### Abnahme

| Kriterium (Plan Phase 5) | Beleg |
|---|---|
| Neue Person startet die App, lädt Beispiel 01, klickt einen Halt an und landet an der richtigen XML-Stelle, ohne Code zu ändern | E2E-Test `example01.spec.ts`: startet den echten Server mit `scripts/start.py`, öffnet Beispiel 01 und die Fahrt, klickt „Interlaken West“; markiert ist `<Name lang="de">Interlaken West</Name>`, Randbeschriftung und erstes Glied der Herkunftskette zeigen `ServiceFrame` in der Farbe aus `config/frame-colors.json`, das zweite Glied `ScheduledStopPoint`; Konsole ohne Fehler. README: Abschnitte „Starten und beenden“ und „Bedienung“ (Schritte 1–3) beschreiben genau diesen Weg. |
| … ohne Code zu ändern / frische Einrichtung nach README | Frischer Klon des Repositorys in einem leeren Ordner (neben dem Guide-Klon): `uv sync` legte `.venv` an, `scripts/start.py` führte `npm ci` und `npm run build` aus dem leeren `dist` aus und startete den Server (`/api/guide` antwortet mit Branch `next`, Commit `b7ac158`, XSD vorhanden); in diesem Klon bestand der E2E-Test. **Nicht geprüft:** Installation der Voraussetzungen (Homebrew, Node, Git) und das Klonen des Guides von GitHub auf einem frischen Rechner (nichts heruntergeladen ausser dem Browser des E2E-Tests). |
| Hilfeseite zeigt aktuelle Farben | `test_help_data_shows_the_current_config_and_all_checks` (Daten der Seite = `config/frame-colors.json`, `config/not-relevant-elements.json`); Vitest „zeigt jede Frame-Farbe und jede Grau-Element der Daten, nicht mehr und nicht weniger“; Hilfeseiten-Test auf Texte in beiden Sprachen (Phase 0). |
| … durchgeführte und nicht durchgeführte Prüfungen | Daten der Seite = Liste `CHECK_STEPS` (gleicher Test, mindestens eine nicht durchgeführte Prüfung); Vitest „ordnet jede Prüfung der Daten genau einer der beiden Listen zu und nennt Quellen“ (Quelle bzw. Stand „später“/„noch nicht umgesetzt“). Sichtprüfung im Browser (Chrome) am Ende der Hilfeseite: Guide-Stand mit Branch, Commit, XSD und Teststand. |
| Sprachdatei-Prüfung | Bestehend (Phase 0–4): gleiche Schlüssel in beiden Dateien, keine leeren Texte, alle im Code verwendeten festen Schlüssel vorhanden, Test „keine festen Texte im Frontend-Code“, Hilfetexte für Funktionen, Prüfschritte, Schweregrade, Farben, Meldungen. **Neu:** `test_no_unused_texts` (ungenutzte Schlüssel; berücksichtigt Aufzählungen und zusammengesetzte Schlüssel wie `feature.${id}.title`) und `test_every_composed_key_pattern_matches_a_text`. Ergebnis: alle 416 Schlüssel belegt, nichts zu entfernen. |
| README vollständig | Installation (geprüft, unverändert gültig), Start und Beenden, Bedienung, Tests inklusive E2E, Windows-Testanleitung (angepasst an Datei öffnen, Prüfen, Hilfe), vollständige bekannte Grenzen. |

### Wichtigster Befund der Phase

`scripts/start.py --port <Port>` (im README als Option genannt) setzte nur den Port des Servers; die Origin-Prüfung erwartete weiter den Port aus `config/settings.json` und wies jede Änderung (Beispiel öffnen, Datei hochladen) mit 403 ab. Gefunden beim ersten E2E-Lauf auf dem Testport; behoben in `5fa264f` (`create_app(..., port)`), Test `test_origin_check_uses_the_port_the_server_runs_on`.

### Selbstkontrolle (Code-Review und Sicherheits-Review über `765613a..7bd8f2b`)

Eigene Durchsicht gegen `CLAUDE.md` und `docs/engineering-guidelines.md`; keine `noqa`, `type: ignore` oder `biome-ignore` hinzugefügt. Funde und Prüfpunkte:

1. **Port der Origin-Prüfung** (siehe oben) behoben und getestet.
2. **E2E gegen fremden Server:** `reuseExistingServer: false` und eigener Testport verhindern, dass der Test gegen einen laufenden Explorer läuft; ist der Port belegt, bricht Playwright mit klarer Meldung ab.
3. **Keine festen Pfade:** Der Test liest Guide-Pfad und Farben aus `config/`; Auswahl der Elemente über CSS-Klassen statt Oberflächentexten (Sprachumschaltung ändert den Test nicht).
4. **Vitest nimmt die E2E-Dateien nicht auf** (`exclude: e2e/**`), TypeScript und Biome prüfen sie mit.
5. **Sicherheit:** Der Server bleibt auf `127.0.0.1`; der Test öffnet nur lokale Adressen; `npm audit` ohne Funde; die Testartefakte (`test-results/`, `playwright-report/`) sind ignoriert. Keine Lieferdaten aus `../netex-files/` verwendet.
6. **Schwäche (nicht behoben, offen):** Das Beenden des Servers durch Playwright (`SIGINT`, Prozessbaum) ist unter Windows nicht geprüft; in der Windows-Testanleitung vermerkt ([open-points.md](open-points.md) 8).

### Gesamtübersicht der bekannten Grenzen und offenen Punkte der ersten Ausbaustufe

Aus den Testberichten der Phasen 0–4, [open-points.md](open-points.md) und [decisions.md](decisions.md); dieselbe Liste in der README („Bekannte Grenzen“).

**Nicht umgesetzt oder nicht eingebunden**
- Rund 330 Schweizer Profilregeln (über das Build-Werkzeug des Guides, später); CH-SJP-08 und CH-SJ-16 bewusst nicht umgesetzt; Erklärungen und Korrekturvorschläge zu XSD-Meldungen.
- Fahrtansicht: `DestinationDisplay`, Takt, Formation, Flügelung, Durchbindung, Bedarfsverkehr, Elternfahrt der Kurswagen (nur im Objekt-Explorer); automatische Prüfung der Betriebstage von Kurswagen und Elternfahrt; Zeitumstellung nur bei auflistbaren `ValidDayBits` (bei 15 von 22 Beispielen weicht deren Länge ab).
- Auswahl mehrerer Guide-Stände, Einstellungsseite für Farben, Zellfarben der Mappingtabelle; Webversion (Pyodide) samt Veröffentlichung und Lizenzklärung der Guide- und XSD-Dateien (info.fachbus@sbb.ch).

**Leistung und Umfang (zurückgestellt bis zu den grossen Lieferungen)**
- 12-GB-Lieferung (NeTEx 1.10): Import aus Ordner, Index auf Festplatte, Hintergrundprozess, angepasste ZIP-Grenzwerte, Lesesperre für `../netex-files/`; offener Punkt 7 (Auflösung und Fahrtansicht mit vielen Einzelabfragen, Referenzen im Speicher, keine Begrenzung der Halte).
- Upload bis 200 MB im Arbeitsspeicher; höchstens 10 offene Datensätze; nur UTF-8/ASCII; `DOCTYPE` abgewiesen; reine CR-Zeilenenden ohne richtige Zeilennummern.

**Inhalt der Guide-Beispiele**
- 121 `order`-Verstösse in 9 Beispielen, 3 Hinweise „Rumpf-Fahrt“ (17), 3 Warnungen CH-JP-01 (21); Kommentar von Beispiel 01 (10:53) weicht von der Rechnung (10:54) ab ([assumptions.md](assumptions.md)); `offical` ist kein Regelverstoss.

**Betrieb und Werkzeuge**
- Guide-Status nur beim Start; Prüfung vor Ende des XSD-Ladens wartet bis zu 17 s; kein Commit-Datum des Guides; `pip-audit`/`npm audit` brauchen Internet; Skriptpaket über 500 kB (CodeMirror); einige SQLite-Datensätze der Tests bleiben ungeschlossen (`ResourceWarning`, harmlos).
- **Windows: nicht getestet** (Start-Skript, Prüfbefehl, E2E-Test, Beenden des Servers).
- Offen beim Benutzer: Glossar Englisch/Deutsch (offener Punkt 2); Bestätigung der technischen Festlegungen „Umsetzung Phase 5“; Entscheid, ob der E2E-Test in den Git-Hook soll.

### Review durch Opus und Korrekturen (01.11.2026)

Code-Review über `765613a..8abb12a`; alle 10 Funde behoben in `87dafe9`. Festlegungen: [decisions.md](decisions.md) „Korrekturen aus dem Review von Phase 5“.

| Fund | Behebung | Test |
|---|---|---|
| 1 `create_app` leert gemeinsames `work/` | Arbeitsordner je Port (`work/<port>/`), Aufräumen beim Beenden; `start.py` bricht bei belegtem Port ab | `test_each_port_has_its_own_work_folder`, `test_close_*`, `test_port_is_free_*` |
| 2 E2E wartet nicht auf XSD/Beispiele | Abfrage von `/api/guide` bis `examplesReady` (120 s) | E2E |
| 3 `guidePath()` ohne Standardwert | Standard `../netexRealisationGuideSwitzerland` | E2E |
| 4–6 Guide-Stand dupliziert, „fehlt <Commit>“, ungestylt | gemeinsame Komponente `GuideFacts` (Status-Box und Hilfeseite), Stil `.guide-facts` | `HelpPage.test.tsx` (Kurz-Commit, fehlende XSD ohne Commit) |
| 7 Dev-Proxy-Port | `NETEX_API_PORT`, README (Tests und Prüfbefehl) | – (Konfiguration) |
| 8–9 Erkennung ungenutzter Schlüssel | nur Zeichenketten des Anwendungscodes (`ast` ohne Docstrings; TypeScript ohne Kommentare, ohne Tests) | `test_comments_and_docstrings_do_not_count_as_use` |
| 10 Origin-Test prüft nur `!= 403` | prüft `== 404` | `test_origin_check_uses_the_port_the_server_runs_on` |

Nachweis: `scripts/check.py` grün; `scripts/test.py` 825 Tests bestanden (Guide b7ac158, XSD 73b337e); Vitest 163 Tests; E2E zweimal bestanden (je rund 19 s), der zweite Lauf, während eine Instanz auf Port 8765 mit hochgeladener Datei lief: `work/8765/` blieb erhalten, nach dem Beenden war `work/` leer.

### Überarbeitung der Oberfläche (01.11.2026)

Gegenstand: Commits `85ad976`, `ff26928`, `142c23a` (Teile A bis C) samt Kern-Erweiterung (`category` der Fahrtenliste, `operator` der Fahrtansicht). Festlegungen: [decisions.md](decisions.md) „Überarbeitung der Oberfläche“ und „Review der Oberflächen-Überarbeitung“.

**Code-Review und Sicherheits-Review** über `4c60efd..HEAD`.

| Fund | Behebung | Test |
|---|---|---|
| Legende der Frame-Farben doppelt (Herkunft zeigen + aufgeklappte Aufbau-Übersicht) | `StructureOverview` zeigt die Legende nur ohne „Herkunft zeigen“ | `JourneyView.test.tsx`, `StructureOverview.test.tsx` |
| Zähltexte ohne Einzahl („1 Betriebstage“, „1 Meldungen, davon Fehler“, „1 Blätter“, „1 Treffer“, Meldungen des Kerns) | Konvention `<Schlüssel>.one` in `translate`, Texte de-CH/en | `i18n.test.ts`, `ExampleList.test.tsx`, `JourneyView.test.tsx`, `test_help_texts.py` |
| Datensatz-Wahl in der Kopfzeile ändert in der Hilfe nichts sichtbar (Ansicht blieb „Hilfe“) | `openDataset` setzt die Ansicht auf die Hauptansicht | `App.test.tsx` |
| Reiter links ohne Tastaturbedienung (alle mit Tab erreichbar, keine Pfeiltasten) | Rollender Tabindex, Pfeiltasten/Pos1/Ende | `SidebarTabs.test.tsx` |
| Kern: Auflösung von `category`/`operator` über (ID, Typ) nicht durch Test belegt | Verhalten war schon richtig; Tests ergänzt (gleiche ID, anderer Typ ⇒ nicht aufgelöst; Kategorie ohne `ShortName` ⇒ fehlt, nichts erfunden) | `test_journeys.py`, `test_journey_view.py` |

Sicherheit: kein `dangerouslySetInnerHTML`, kein `innerHTML`, kein `setAttribute`; `style` nur über React (CSSOM) mit Farben aus `config/` (CSP `style-src 'self'` bleibt streng, keine Inline-Styles im HTML); die neuen API-Felder `category` und `operator` sind Texte aus der Datei (gleiche Umwandlung wie bisherige Angaben), es gibt keine neuen Eingaben und keine neuen Endpunkte. Keine konkreten Funde.

Verloren gegangene Funktionen gegenüber vorher: keine gefunden (Verlauf, Objektansicht, Suche, Diagnosen mit Sprung, Rechenkette, Herkunftskette, XML-Markierung, Datei öffnen, Prüfen inkl. „Trotzdem als CH 2.0 prüfen“, Guide-Status, Sprachwechsel sind erreichbar; „Geöffnete Dateien“ und „Prüfen“ stehen im Reiter „Prüfung“).

Nachweis: `scripts/check.py` grün; pytest 835 Tests, Abdeckung `app/core` 98 %; Vitest 234 Tests; E2E (`npm run e2e`) bestanden (1 Test, rund 19 s).

## Guide-Update d0a8e6d (04.11.2026)

Gegenstand: Guide-Klon von `b7ac158` auf `d0a8e6d` (26 Commits, 27 Dateien); XSD `73b337e`, `general_rules.sch` und Mappingtabelle unverändert. Commits im Projekt: `88c23ad` (Tests, Verweisziele), `2445a17` (fremde Arbeit, nicht Teil dieses Updates), `53790ef` (CH-JP-01), `f8c2d4b` (Belege), `709e669` (Entscheid A), `db1e716` (Entscheid B), dazu dieser Bericht, `decisions.md` und `guide-tested.json`.

### Änderungen im Guide und Auswirkungen

| Änderung im Guide | Auswirkung | Behebung |
|---|---|---|
| Attribut `order` aus allen Beispielen entfernt (rund 120 Stellen) | 121 `order`-Befunde in 9 Beispielen entfallen; Test erwartete 121 | Test prüft jetzt „0 Befunde in allen Beispielen“; die Regel selbst belegen die synthetischen Tests weiter |
| Beispiel 19 gelöscht (`a054e26`), Beispiel 23 neu (`SITE_OFFER`) | 23 nutzt `PlaceRef`/`ParentSiteRef` ohne Eintrag in `config/ref-targets.json` (2 Tests rot); 23 hat einen Befund: `ParentSiteRef` auf `ch:1:sloid:169`, das in der Datei nicht steht (Status „Fehler“, Guide-Datei, nichts geändert) | Einträge aus der XSD abgeleitet (31 bzw. 49 Zieltypen), Test `test_ref_targets` grün |
| Kurswagen offiziell mit `JourneyPart` und `DirectCarriage` | Beispiel 21 hatte 3 Warnungen CH-JP-01; Widerspruch P2/`assumptions.md` Nr. 6 | CH-JP-01 erlaubt `DirectCarriage`; Widerspruch als aufgelöst eingetragen |
| Sonderfall Zeitumstellung: `DepartureTime` in UTC (`02:33:00Z`) | `parse_time_of_day` lehnte `Z` ab („nicht berechenbar“) | Entscheid A: UTC lesen, nicht umrechnen, kennzeichnen ([mapping.md](mapping.md) Z9) |
| Bezüge der Kurswagen-Teilstrecken auf das Fahrtmuster der ziehenden Fahrt (`uc05` Z. 154) | Teilstrecken waren bewusst nicht den Halten zugeordnet | Entscheid B ([mapping.md](mapping.md) P3) |
| `STOP_OFFER` → `SITE_OFFER`, `StopPlace`-Vorlage erweitert, `uc05` Usage Notes umformuliert | Texte in `mapping.md` H7, `guide-2.0.md`; A7 („overrides“ ist jetzt „valid for this part only“, `uc05` Z. 155; Frage ergänzend/ersetzend bleibt offen) | Belege nachgeführt |

### Belegprüfung

Per Skript (`python3 -I`, nur lesend; Zeilen von `b7ac158` per Diff auf `d0a8e6d` abgebildet, Zitate in „…“ gegen die Datei geprüft) über `mapping.md`, `core-rules.md`, `research/guide-2.0.md` und `assumptions.md`:

- **189 Zeilenverweise** gefunden: **153 unverändert**, **14 automatisch verschoben** (`08_timetable.md` +4 Zeilen, `03_xml_modelling.md` +4 Zeilen), **22 mit geänderter Zeile** (Inhalt der Stelle neu geschrieben oder gelöscht) und von Hand geprüft: 3× `02_files.md` Z. 160–165 → Z. 163, `02_files.md` Z. 142 (Inhalt `SITE_OFFER`), `uc05` Z. 104 → Z. 155 (Text geändert), `uc08` Z. 43 (Text ersetzt), `JourneyPart.xml` Z. 86–90 → 86–89, `uc05` Z. 5–7/24–66 → Z. 9, 22–25, 29–66, 68–110; 6 Verweise waren Zeilen in Beispieldateien (Beispiele 08 und 21, Zeilen unverändert, von Hand bestätigt); übrige Meldungen waren eigene Formulierungen in Anführungszeichen, keine Guide-Zitate.
- Nach der Nachführung: **220 Verweise** erneut geprüft (Datei und Zeile vorhanden), keine Abweichung ausser den 3 Zeilen in Beispieldateien (Skript kennt sie nicht).
- Commit-Angaben in den Belegen stehen überall dort auf `d0a8e6d`, wo geprüft; Stellen, die ausdrücklich den früheren Stand beschreiben (Beispiel 19, „overrides“, Messungen der `order`-Befunde), nennen `b7ac158` mit diesem Vermerk.
- **Zählungen der Beispiele** (`core-rules.md`, Kernregeln) neu erhoben, weil Beispiel 19 fehlt: 37 `ServiceJourney` (vorher 39), 36 `ServiceJourneyPattern` (38), 201 `StopPointInJourneyPattern` (206), 34 `TimeDemandType` (36), 133 `JourneyRunTime` (136), 24 `JourneyWaitTime` (25), 119 `TimingLink` (121), 5 `JourneyPart`; `ServiceJourneyPatternType` fehlt in 24 von 36 Mustern in 14 von 22 Beispielen; `ServiceAlteration` in 34 von 34 Fahrten mit Muster; `sjyid` fehlt in 8 von 37 Fahrten (6 Beispiele). Kernregel-Verstösse: unverändert nur die 3 Rumpf-Fahrten in Beispiel 17. `ValidDayBits`-Tabelle (`assumptions.md` Nr. 3) unverändert gültig.

### Beispielstatus (`guide-tested.json`, Guide `d0a8e6d`, XSD `73b337e`)

22 Beispiele: **20 ohne Meldungen**, 1 mit Hinweisen, 1 mit Fehler (vorher: 12 / 1 / 9). Gewechselt auf „ohne Meldungen“: 02, 03, 08, 12, 14, 20, 21, 22 (waren nur wegen `order` bzw. CH-JP-01 auffällig). Beispiel 19 weg, Beispiel 23 neu mit dem einen Befund (`ParentSiteRef`).

### Tests

- `scripts/check.py` grün bei jedem Commit (Hook): ruff, mypy --strict, pytest, Biome, Vitest, Build, pip-audit, npm audit.
- pytest **866 Tests bestanden** (Stand vor dem Update 835 + Entscheid-Tests), Abdeckung `app/core` **98 %**; Vitest **279 Tests**; E2E (`npm run e2e`) bestanden (1 Test, rund 20 s); `scripts/test.py` bestanden, `guide-tested.json` auf `d0a8e6d` geschrieben.
- Neue Tests: `parse_clock` (UTC, andere Zonen), UTC-Fahrt mit synthetischer Datei `fixtures/ch20_utc_departure.xml` (Kern, API, Vitest für `TimeCell`/`CalculationChain`/`timeWithDay`), kein Vergleich mit Zeiten der `JourneyPart`, kein Hinweis „Nacht der Zeitumstellung“ für UTC-Zeiten, Zuordnung der Kurswagen-Teilstrecken (Beispiel 21: Positionen 1–2, 2–3, 3–4; kein Treffer; mehrdeutiger Treffer), CH-JP-01 mit `DirectCarriage` und unerlaubtem Wert, Beispiel 21 ohne CH-JP-01-Befund.

### Selbstkontrolle

Code- und Sicherheitsüberlegung zu den Änderungen: UTC wird nur als Kennzeichen geführt (kein Datum, keine Zonenregeln, keine Ersatzwerte); andere Zeitzonen bleiben „nicht berechenbar“. Die Zuordnung der Teilstrecken rät nicht (genau ein Treffer, sonst keine Zuordnung). Keine neuen Abhängigkeiten, keine Datenwerte als HTML (nur React-Text), keine Pfade in der API. Hilfeseite (`feature.midnight.description`, `feature.offers.description`, `part.notPlaced`) und Texte de/en nachgeführt; `tests/test_help_texts.py` grün.

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

## Phase 1: Einlesen und Objekt-Explorer (31.10.2026)

Umsetzung: Commits `fe208d5` und `5bfb694` (Funde aus dem Code-Review). Umgebung wie Phase 0. Guide `b7ac158`, XSD `73b337e`.

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

### Code-Review (eingebaute Prüfung `/code-review`, Stufe high, über `927633e..fe208d5`)

10 Funde, alle behoben in `5bfb694`:

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

### Sicherheits-Review (eingebaute Prüfung `/security-review`, über `927633e..5bfb694`)

**Keine Funde.** Geprüft: Path Traversal beim Öffnen von Beispielen (nur Namen aus der Beispielliste), XXE (`DOCTYPE` abgewiesen), SQL (nur feste Teile, Werte als Parameter), IDs (zufällig, Format geprüft), XSS (kein `innerHTML`, CodeMirror-Beschriftungen über `textContent`). Vorübergehende lokale Referenz `origin/HEAD` wie in Phase 0, danach gelöscht.

Eigener Fund bei der Browser-Prüfung: Die strenge CSP blockierte die Stile von CodeMirror (`<style>`-Element). Gelöst ohne CSP-Lockerung durch einen Shadow-DOM (Entscheid „Umsetzung Phase 1“, Punkt 6).

### Lücken und Hinweise

- Referenzen nur als Grundstufe (Phase 2: Versionen, Rückwärtsreferenzen, `external_or_unloaded`, Referenzdiagnosen).
- Der Build meldet ein Skriptpaket über 500 kB (CodeMirror). Für die lokale Nutzung unkritisch; bei der Webversion prüfen.
- Dateien mit nur CR als Zeilenumbruch (ohne LF) werden in den Zeilennummern nicht unterstützt; in der Praxis nicht anzutreffen.
- Windows: nicht getestet.

## Phase 2: Referenzen und Herkunft (31.10.2026)

Umsetzung: Commits `ff81a5d` und `17e08dc` (Funde aus dem Code-Review). Umgebung wie Phase 0. Guide `b7ac158`, XSD `73b337e`.

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

### Code-Review (eingebaute Prüfung `/code-review`, Stufe high, über `7e69a47..ff81a5d`)

9 Funde. Behoben in `17e08dc`:

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

### Sicherheits-Review (eingebaute Prüfung `/security-review`, über `7e69a47..17e08dc`)

**Keine Funde.** Geprüft: SQL (nur Platzhalter und feste Spaltennamen, alle Werte als Parameter), neuer Aufruf `GET /api/objects/{id}/provenance` (nur zufällige Datensatz-ID plus Elementnummer, kein Pfad), `config/ref-targets.json` (Grösse, JSON-Form und Namensmuster geprüft), keine neue XML-Verarbeitung (`DOCTYPE`-Abweisung gilt weiter), Frontend (Werte nur als Text, Farben nur aus validiertem `#RRGGBB`), keine Datenpreisgabe über den bereits geöffneten Datensatz hinaus. Die eingebaute Prüfung vergleicht mit `origin/HEAD`; das Repository hat kein Remote, deshalb wurde vorübergehend eine lokale Referenz auf `7e69a47` angelegt und danach gelöscht.

### Review durch Opus und Korrekturen (über `7e69a47..fdd2408`)

Funde und Entscheide des Benutzers (31.10.2026) sind in [decisions.md](decisions.md) „Entscheide nach Review Phase 2“ festgehalten. Korrekturen in den Commits `8750672` (Entscheide) und `f2842e6` (Frontend) sowie im Commit „Korrekturen aus dem Review Phase 2“ (Backend).

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

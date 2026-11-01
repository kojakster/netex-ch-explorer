# NeTEx CH Explorer – Umsetzungsplan, erste Ausbaustufe

**Status:** **Freigegeben** durch den Benutzer am 31.10.2026. Ersetzt den ursprünglichen Plan `NETEX_EXPLORER_IMPLEMENTATION_PLAN.md` (im Git-Verlauf, Commit `4e8e378`). **Umgesetzt:** Phasen 0–5 der ersten Ausbaustufe abgeschlossen am 01.11.2026; Nachweis je Phase in [docs/test-report.md](docs/test-report.md), bekannte Grenzen im README und im Testbericht.
**Stand:** 01.11.2026
**Massgebend für Details:** [docs/decisions.md](docs/decisions.md). Bei Abweichungen gilt `decisions.md`; der Widerspruch wird dem Benutzer vorgelegt.
**Abgleich mit dem ursprünglichen Plan:** [docs/plan-abgleich.md](docs/plan-abgleich.md)

## 1. Ziel

Ein lokales Werkzeug, mit dem man Schweizer NeTEx-Dateien **visuell und selbsterklärend versteht**: woher jede angezeigte Angabe stammt und wie die Datei aufgebaut ist.

Man wählt ein Beispiel aus dem CH-NeTEx-Guide oder öffnet eine eigene Datei. Dann

- sieht man eine einzelne Fahrt **wie einen Fahrplan**,
- erkennt an **klaren Farben**, aus welchem Frame jede Angabe stammt,
- verfolgt jede Angabe über eine sichtbare Kette bis zur **exakten Stelle im XML**,
- erkundet **alle Objekte der Datei** und ihre Verweise vor- und rückwärts,
- erkennt **Fehler** mit Stelle und Verweis auf das Guide-Kapitel.

Massstab: Der Fahrplan mit nachvollziehbarer Herkunft ist wichtiger als Such- oder Komfortfunktionen.

Grundsätze (aus [CLAUDE.md](CLAUDE.md)): klein und wartbar vor ausgefeilten Funktionen; Aufwand offenlegen; Unklarheiten dem Benutzer vorlegen. **Codequalität** nach [docs/engineering-guidelines.md](docs/engineering-guidelines.md): keine Sicherheitslücken, wartbar, erweiterbar, keine Abkürzungen; technisch erzwungen und pro Phase nachgewiesen.

## 2. Umfang

### Erste Ausbaustufe (dieser Plan)

1. Lokale Anwendung: Start per Skript, Bedienung im Browser.
2. Guide als Git-Klon im Nachbarordner (VS-Code-Workspace); das Tool zeigt den Guide-Commit an und meldet, wenn er neuer ist als zuletzt getestet oder die XSD fehlt.
3. Alle Dateien in `src/examples/` des Guide-Stands einzeln ladbar, auch fehlerhafte oder noch nicht aktualisierte; Status pro Beispiel in der Auswahlliste.
4. Nach dem Laden: Liste der Fahrten der Datei (Zugnummer, Linie, erster/letzter Halt) und eine **einfache Objektsuche** nach ID oder Name. Keine weitergehende Suche (Schwerpunkt ist die Fahrplandarstellung mit Herkunft).
5. Fahrtansicht für eine `ServiceJourney` als Fahrplan: Halte mit Ein-/Aussteige-Eigenschaften, Ankunft/Abfahrt (auch berechnete Zeiten), Mitternacht, Betriebstage, Angebote.
6. Herkunft jeder angezeigten Angabe bis zur exakten Stelle im XML.
7. Visuelle Führung: klare Frame-Farben mit Legende, Herkunftskette als farbige Kästchen, XML-Ansicht mit farbigen Frame-Bereichen; Farben in `config/frame-colors.json` einstellbar.
8. Objekt-Explorer mit Referenzen vor- und rückwärts und Frame-Zugehörigkeit.
9. Stammdaten: Code und Bedeutung aus der Mappingtabelle.
10. Eigene Dateien öffnen: XML, mehrere XML, ZIP.
11. Validierung Grundstufe: XSD, die 4 allgemeinen Guide-Regeln (`general_rules.sch`) und ~20 Schweizer Kernregeln für den Fahrplan, mit Stelle und Link zum Guide-Kapitel.
12. Hilfeseite: Funktionen, Frame-Farben, durchgeführte und nicht durchgeführte Prüfungen (automatisch aus den Daten).
13. Oberfläche in Deutsch und Englisch, alle Texte in Sprachdateien.

### Später (nicht in diesem Plan, Schnittstellen nicht verbauen)

- Webversion (statisch, Pyodide). Der Kern wird dafür von Anfang an ohne Server-Abhängigkeiten gebaut.
- Validierung: deutsche Erklärungen und Korrekturvorschläge.
- Auswahl mehrerer Guide-Stände in der Oberfläche (mehrere Guide-Klone, Pfade konfigurierbar).
- Grosse Lieferungen (z. B. 1.10-Lieferung, 12 GB), Adapter für CH 1.10.
- Weitere Oberflächensprachen.
- Übrige Schweizer Profilregeln aus den Guide-Vorlagen (~330 Regeln) über das Build-Werkzeug des Guides.
- Einstellungsseite für die Farben in der Oberfläche.
- Auswertung der Zellfarben der Mappingtabelle (neu / nicht mehr verwendet) für die Validierung.

### Nichtziele

- Kein Fahrplanauskunftssystem, keine Verbindungssuche, keine Gesamtnetz-Darstellung.
- Keine Korrektur oder Veränderung von Dateien; das Tool liest nur.
- Keine Profile anderer Länder.
- Keine Suche nach Linie, Zugnummer oder Haltestelle.
- Keine eigene Darstellung der Haltestellen-Ausstattung (Toiletten, Automaten usw.); sie bleibt im Objekt-Explorer sichtbar und wird grau dargestellt.
- Keine Aussage „gültig“ nur weil eine Datei lesbar ist; Prüfungen gegen den Entwurf heissen „geprüft gegen Entwurf <Commit>“.

## 3. Verbindliche Regeln für Daten und Anzeige

| Regel | Umsetzung |
|---|---|
| **Herkunft** | Jede angezeigte Angabe hat eine Herkunft: Objekt, Frame, Datei, Zeile/Spalte, Pfad. Ein Klick markiert die exakte Stelle im XML. Abgeleitete Angaben zeigen die Kette ihrer Quellen. |
| **Nichts erfinden** | Fehlendes oder nicht Auflösbares wird als solches angezeigt („nicht in dieser Datei aufgelöst“, „nicht berechenbar“), nie durch Standardwerte ersetzt. Unsicherheiten (z. B. unklare Zuordnung) werden **in der Anwendung** sichtbar gemacht, nicht nur in `docs/assumptions.md`. |
| **Fehlend ≠ fehlerhaft** | Was laut Guide nicht in der Datei steht, ist kein Fehler: z. B. Haltestellen in einer `NETWORK_OFFER`-Datei (kommen laut Guide aus ATLAS; Beispiel 18 hat keinen `SiteFrame`) oder Ziele in einer nicht geöffneten Datei. Anzeige „nicht in dieser Datei (extern bzw. nicht geladen)“, Referenzstatus `external_or_unloaded`. |
| **Begriffe nicht vermischen** | `ScheduledStopPoint` (Fahrplanpunkt), `StopPlace` (Haltestelle) und `Quay` (Kante) werden getrennt beschriftet und angezeigt. |
| **XML bleibt XML** | Werte, Codes und Texte aus den Dateien werden unverändert angezeigt, nie übersetzt. Mehrsprachige Texte: alle Fassungen mit Sprachkennzeichen, auch die in NeTEx 2.x gültige verschachtelte Form (`<Text lang="en">…<Text lang="de">…</Text></Text>`, z. B. Beispiele 05, 16). Der NeTEx-Elementname wird immer mit angezeigt. |
| **Codes und Stammdaten** | Immer den gesendeten Code zeigen. Bedeutung nur aus der Datei selbst oder aus der Mappingtabelle (mit Blatt, Zeile, Guide-Stand), sonst „keine Erläuterung in den Stammdaten“. |
| **Frames** | Frame-Typ und Frame-ID aus der tatsächlichen XML-Struktur; Frame ist eindeutig als (Datei, Frame-ID). |
| **Robustheit** | Fehlerhafte Dateien werden so weit wie möglich geladen; Fehler erscheinen als Diagnose, nie als Absturz. |
| **Diagnosen getrennt** | Arten: Datei/ZIP, XML-Syntax, XSD, Profilregel (Schematron), Referenz (`unresolved`, `ambiguous`, `external_or_unloaded`), Projektion (z. B. „nicht berechenbar“, Widerspruch). Nie vermischen. |
| **Schweregrade** | Drei Stufen, jede mit Symbol **und** Text: **⚠ Fehler** (verletzt XSD oder Regel, Datei kaputt), **Warnung** (vermutlich problematisch, z. B. Widerspruch zwischen berechneter Zeit und `JourneyPart`), **ℹ Hinweis** (kein Fehler, nur zum Verständnis, z. B. `external_or_unloaded`, fehlendes `DepartureDayOffset` → Standardwert 0, Nacht der Zeitumstellung). |

## 4. Datenquellen

### Guide-Stand

- Der Benutzer klont den Guide mit Git nach `../netexRealisationGuideSwitzerland/` (Branch `next`) und holt das XSD-Submodul (`git submodule update --init --depth 1`). Kein eigener Download-Code. Exakte Befehle für macOS und Windows im README.
- VS-Code-Workspace `netex-ch-explorer.code-workspace` (im Projekt) zeigt Projekt und Guide nebeneinander; `netex-files/` gehört nicht dazu.
- Das Tool liest den Guide über den konfigurierten Pfad (Standard `../netexRealisationGuideSwitzerland`) und ermittelt den Commit direkt aus dem `.git`-Ordner (ohne Git-Programm); Anzeige in der Oberfläche mit „in Entwicklung“.
- Daraus genutzt: `src/examples/*.xml` + `README.md` (Titel), `src/templates/` (später für Vorschläge), `src/schematron_rules/general_rules.sch`, `xsd/`, `src/A5_annex_index.md` (Element → Kapitel), `src/media/Mappingtabellen_NeTEx_v2.0.xlsx`.
- Aktualisieren: `git pull` + `git submodule update --init --depth 1`.
- **Sicherheitsnetz:** `guide-tested.json` im Projekt hält fest, mit welchem Guide-Commit die Tests zuletzt erfolgreich liefen, und **pro Beispiel** Prüfsumme (SHA-256) und Ergebnis (ohne Meldungen / mit Hinweisen / mit Fehlern / nicht lesbar). Wird nur vom Testlauf `scripts/test.py` geschrieben. Ist der vorhandene Stand neuer: Hinweis „Guide-Stand neuer als zuletzt getestet – Tests ausführen“; geänderte oder neue Beispiele werden einzeln erkannt. Fehlt die XSD: Hinweis mit dem fehlenden Befehl.
- **Teilweise aktualisierte Guides:** Beispiele können in unterschiedlichem Stand sein (heute z. B. 2 Beispiele mit `version="1.09"`, README der Beispiele noch mit altem Zeitmodell). Jede Datei wird für sich geladen und erkannt; ein veraltetes oder fehlerhaftes Beispiel beeinträchtigt die anderen nicht. Die Fahrtansicht zeigt, was sich auflösen lässt, der Rest erscheint als „nicht berechenbar“ mit Grund.

### Mappingtabelle

Wird beim Start aus der Excel-Datei des Guide-Klons gelesen (Spalten über ihre Namen; Zellfarben ignoriert; Zwischenspeicher je Commit erlaubt). Fehlt eine erwartete Spalte: Hinweis in der Oberfläche, betroffene Bedeutungen fehlen, nichts wird geraten.

### Eigene Dateien

XML, mehrere XML oder ZIP **nur über den „Datei öffnen“-Dialog im Browser**; die Dateien gehen an das lokale Backend. Keine Pfadeingabe (Ordner-Import erst mit grossen Lieferungen). Zuerst Versionserkennung, dann Prüfung (siehe Abschnitt 8).

## 5. Architektur

```text
netex-ch-explorer/
├── app/
│   ├── core/       Python-Paket ohne Server-Abhängigkeiten (läuft später auch unter Pyodide)
│   │   ├── reader/        Einlesen mit pyexpat: Objekte, Referenzen, Frames, Positionen
│   │   ├── index/         SQLite (im Arbeitsspeicher): Objekte, Referenzen, Pfadformen, Diagnosen
│   │   ├── guide/         Guide-Stand, Beispiel-Liste, Mappingtabelle, Kapitel-Index
│   │   ├── profiles/      Versionserkennung; Adapter „generisch“ und „CH 2.0“
│   │   ├── projection/    Fahrtansicht CH 2.0 mit Herkunft je Feld
│   │   └── validation/    XSD und Schematron (lxml)
│   ├── server/     FastAPI, nur dünne Schicht über core; bindet an 127.0.0.1
│   └── frontend/   React + TypeScript + Vite, CodeMirror 6, Sprachdateien
├── scripts/        start.py, test.py (schreibt guide-tested.json bei Erfolg), check.py (alle Qualitätsprüfungen); start.sh/start.ps1 als Einzeiler
├── .githooks/      pre-commit ruft check.py auf (aktiviert mit git config core.hooksPath .githooks)
├── netex-ch-explorer.code-workspace   VS-Code-Workspace: Projekt + Guide-Klon
├── guide-tested.json                  zuletzt erfolgreich getesteter Guide-Commit
├── config/         Einstellungsdateien (Farben, graue Elementtypen, Pfade, Grenzwerte)
├── fixtures/       eigene synthetische Testdateien (keine Guide-Kopien)
├── work/           geöffnete eigene Dateien (nicht versioniert, wird aufgeräumt)
└── docs/
```

| Baustein | Festlegung |
|---|---|
| Python | 3.12+ (lokal 3.13); Umgebung und Pakete mit **uv** (`pyproject.toml`, `uv.lock`). So wenige Abhängigkeiten wie möglich (FastAPI, uvicorn, lxml; Tests: pytest). |
| Frontend-Pakete | **npm** (`package.json`, `package-lock.json`), Node.js 22. |
| Einstellungen | Ordner `config/`: `frame-colors.json`, `not-relevant-elements.json`, `settings.json` (Guide-Pfad, Sprache, ZIP-Grenzwerte). Ungültig/fehlend → Standardwert + Hinweis. |
| Einlesen | **pyexpat**: pro Element Byte-Offset, Zeile, Spalte; eigene Verschachtelungs- und Namespace-Behandlung; Kommentare werden für die Versionserkennung gelesen. Keine externen Entitäten, kein Netzwerkzugriff. |
| Index | SQLite im Arbeitsspeicher je geöffnetem Datensatz; Datei wird beim Öffnen direkt eingelesen (keine Datenbankdatei, kein Hintergrundprozess). Pfadformen einmal in eigener Tabelle; Objekte speichern Datei, Offset, Zeile, Spalte, Frame. Vollständiger Pfad mit Positionsnummern wird beim Anzeigen berechnet. |
| Referenzen | Aus allen `…Ref`-Elementen (auch in `Extensions`). Auflösung über (ID, erwarteter Typ aus Ref-Name bzw. `nameOfRefClass`); `version` und `versionRef` beide lesen. Status: `resolved`, `unresolved`, `ambiguous`, `external_or_unloaded`. |
| Prüfung | lxml nur für XSD und Schematron. |
| Oberfläche | React + TypeScript + Vite; CodeMirror 6 (nur lesen, exakte Bereichsmarkierung, Frame-Bereiche farbig am Rand); keine Graph-Bibliothek. |
| Texte | Keine Texte im Code. Sprachdateien `de-CH.json`, `en.json`; Kern liefert Schlüssel + Parameter; kleine eigene Übersetzungsfunktion. Deutsche Fachbegriffe vorläufig bis zum Glossar. |
| Plattformen | macOS und Windows (Windows wichtiger als Webversion). Skripte in Python, `start.sh`/`start.ps1` nur Einzeiler; `pathlib`, UTF-8 explizit, Dateien sauber schliessen. Bis zum Windows-Test als „nicht getestet“ gekennzeichnet. |

### Schnittstelle (lokal, JSON)

| Aufruf | Zweck |
|---|---|
| `GET /api/guide` | Guide-Status (Pfad, Branch, Commit, Datum, getestet/neuer als getestet, XSD vorhanden, Probleme Mappingtabelle) und Liste der Beispiele mit Titeln |
| `POST /api/datasets` | Datensatz öffnen: Beispiel-Name oder eigene Datei(en)/ZIP |
| `GET /api/datasets/{id}` | Dateien, Versionserkennung, Anzahl Diagnosen |
| `GET /api/datasets/{id}/journeys` | Liste der Fahrten der Datei (Zugnummer, Linie, erster/letzter Halt) |
| `GET /api/datasets/{id}/objects?type=&q=&limit=&offset=` | Einfache Objektsuche nach ID oder Name, paginiert |
| `GET /api/objects/{id}` | Eigenschaften mit Herkunft, Frame, Referenzen ein-/ausgehend |
| `GET /api/objects/{id}/xml` | XML-Ausschnitt mit Positionen für die Markierung |
| `GET /api/journeys/{id}` | Fahrtansicht mit Herkunft je Feld |
| `GET /api/datasets/{id}/diagnostics?category=&severity=` | Diagnosen |
| `POST /api/datasets/{id}/validate` | XSD-/Schematron-Prüfung starten |

Typsichere Antwortmodelle, einheitliches Fehlerformat, begrenzte Antwortgrössen (z. B. XML-Ausschnitt), Texte nur als Schlüssel. Vertrag in `docs/api.md`.

## 6. Fachliche Abbildung CH 2.0 (Fahrtansicht)

Jede Regel wird in `docs/mapping.md` mit Guide-Datei, Abschnitt und Commit belegt. Grundlage: [docs/research/guide-2.0.md](docs/research/guide-2.0.md).

| Inhalt | Abbildung im Guide | Anzeige |
|---|---|---|
| Haltefolge | `ServiceJourney` → `ServiceJourneyPatternRef` → `StopPointInJourneyPattern` (Reihenfolge = **Reihenfolge im XML** laut `03_xml_modelling.md`; das Attribut `order` ist laut `general_rules.sch` nicht erlaubt, steht aber in 95 Halten der Beispiele; weicht es ab → Hinweis) → `ScheduledStopPoint` → `PassengerStopAssignment` → `StopPlace`/`Quay` | Halte in Reihenfolge, Name aus der Datei, Kante falls zugeordnet; fehlt die Zuordnung (z. B. `NETWORK_OFFER`), Hinweis „Haltestelle nicht in dieser Datei“ |
| Halt-Eigenschaften | `StopPointInJourneyPattern`: `ForBoarding`, `ForAlighting`, `RequestStop`, `StopUse` | Pro Halt sichtbar: nur Einsteigen, nur Aussteigen, Bedarfshalt (in den Beispielen häufig: 49× `ForBoarding false`, 36× `ForAlighting false`); Werte mit Herkunft |
| Fahrtbezeichnung | `TrainNumberRef` → `TrainNumber`; `privateCodes/PrivateCode` (`type="sjyid"`); Linie | Zugnummer und Linie im Kopf der Fahrtansicht |
| Zeiten | `DepartureTime` + `TimeDemandTypeRef` → `JourneyRunTime`/`JourneyWaitTime` je `TimingLink` | Ankunft/Abfahrt wie ein Fahrplan, Markierung „berechnet“, Rechenkette mit Quellen; fehlt ein Summand: „nicht berechenbar“ |
| Mitternacht | `DepartureDayOffset` (fehlend = 0, als Standardwert gekennzeichnet); Tageswechsel während der Fahrt nur rechnerisch; `JourneyPart` mit `Start-/EndTimeDayOffset` | „+1“/„−1“ je Zeit, ausdrücklich oder berechnet; Widersprüche als Diagnose; Hinweis in Nächten der Zeitumstellung |
| Betriebstage | `AvailabilityConditionRef` → `AvailabilityCondition` (`FromDate`, `ToDate`, `ValidDayBits`); `DayType` nur Feiertage | Gültigkeitszeitraum und Anzahl Tage; Liste der Tage aufklappbar. Keine Pauschalaussagen wie „Mo–Fr“ |
| Linie, Verkehrsmittel | `LineRef` im `ServiceJourneyPattern`; `TransportMode`/Submode; `TypeOfProductCategoryRef` | Text aus der Datei, Codes mit Stammdaten |
| Angebote | Facilities/`ServiceFacilitySet`, auch nur auf Teilstrecken bzw. an einzelnen Tagen (`JourneyPart`) | Code + Bedeutung aus Mappingtabelle; Gültigkeit (Teilstrecke/Tage) mit Herkunft |
| Hinweise | `NoticeAssignment` → `Notice/Text` | Text unverändert, alle Sprachen |

Nicht eigens dargestellte Inhalte (Kurswagen, Formation, Flügelung, Durchbindung, DRT) sind über den Objekt-Explorer vollständig einsehbar; Erweiterung der Fahrtansicht nach Bedarf.

## 7. Oberfläche

Ziel: **visuell und selbsterklärend** verstehen, woher Angaben stammen und wie eine NeTEx-Datei aufgebaut ist. Visualisiert werden alle Daten der Datei; Ausstattung von Haltestellen (Toiletten, Ticketautomaten usw.) erhält keine eigene Darstellung, bleibt im Objekt-Explorer und XML aber sichtbar (grau). Barrierefreiheit gehört zum Fahrplan.

**Frame-Farben als roter Faden** (klare Farben; Standardwerte in `config/frame-colors.json`, änderbar ohne Codeänderung, ungültige/fehlende Einträge → Standardwert; Legende immer sichtbar, immer mit Frame-Name als Text). Kleinster Farbabstand ΔE76 = 33, Schriftkontrast ≥ 4,5:1:

| Bedeutung | Farbe | Wert | Schrift |
|---|---|---|---|
| `TimetableFrame` | Blau | `#0057B8` | weiss |
| `ServiceFrame` | Grün | `#1B8A2F` | schwarz |
| `SiteFrame` | Orange | `#F57C00` | schwarz |
| `ServiceCalendarFrame` | Gelb | `#FFD600` | schwarz |
| `ResourceFrame` | Rot | `#D32F2F` | weiss |
| `CompositeFrame` | Violett | `#7B1FA2` | weiss |
| unbekannter Frame | Braun | `#6D4C2F` | weiss |
| für den Fahrplan nicht relevant | Grau | `#8A8A8A` | schwarz |

**Grau** bedeutet „für den Fahrplan nicht relevant“, nicht einen Frame; der Frame-Name bleibt als Text sichtbar. Startliste in `config/not-relevant-elements.json` (Entscheid „Startliste Grau“): Haltestellen-Ausstattung (`SiteFacilitySet`, Equipment, Lifte), Wege und Zugänge, Points of Interest, Adressen, Hilfsdienste, Tarifzonen. **Nicht grau:** `StopPlace`, `Quay`, `TopographicPlace`, `FlexibleStopPlace` und Barrierefreiheit (`AccessibilityAssessment`). Neue Fälle bei der Umsetzung dem Benutzer vorlegen. Eine Einstellungsseite in der Oberfläche ist später möglich.

Fehler werden mit Symbol ⚠ und Text gezeigt, nicht nur mit Rot (Verwechslung mit `ResourceFrame`).

- Für Desktop ausgelegt; bei schmalerem Fenster bedienbar.
- **Links oben: Guide-Status-Box** (Sicherheitsnetz, weil der Benutzer den Guide selbst per Git aktualisiert): Profil und „in Entwicklung“, Branch, Commit, Datum; ✔ „getestet“ bzw. ℹ „neuer als zuletzt getestet“ mit Hinweis `scripts/test.py`; ⚠ „XSD fehlt“ mit dem fehlenden Git-Befehl; ⚠ Probleme mit der Mappingtabelle.
- **Links:** Auswahl der Beispiele mit **Status pro Beispiel** (✔ ohne Meldungen · ℹ/⚠ mit Hinweisen/Fehlern und Anzahl · ✖ nicht lesbar · „geändert seit letztem Test“ / „neu“) bzw. „Datei öffnen“, Versionserkennung, Liste der Fahrten der Datei, einfache Objektsuche, Diagnosen.
- **Mitte:** umschaltbar „Fahrt“ / „Objekt“.
  - Fahrt: Kopf mit Zugnummer, Linie, Verkehrsmittel, Betriebstagen; Tabelle Halt – Ein-/Aussteigen – Ankunft – Abfahrt – Angebote. **Jede Angabe trägt die Farbmarkierung ihres Frames.**
  - Objekt: Eigenschaften und Referenzen ein-/ausgehend als **farbige Liste** (Farbe des Ziel-Frames), jede anklickbar.
- **Rechts:** **Herkunftskette** der gewählten Angabe als farbige Kästchen in einer Reihe (z. B. `ServiceJourney` → `ServiceJourneyPattern` → `ScheduledStopPoint` → `PassengerStopAssignment` → `StopPlace`), jedes Kästchen anklickbar; bei berechneten Werten die Rechenkette. Darunter XML-Ausschnitt mit exakter Markierung und **Frame-Bereichen farbig am Rand**.
- Klick auf eine Angabe synchronisiert Auswahl, Herkunftskette und XML-Markierung. Zurück-Navigation (Verlauf) bleibt erhalten.
- Keine Graph-Bibliothek; einfache Kästchen in HTML/CSS.
- Sprachumschaltung Deutsch/Englisch.
- **Hilfeseite** über einen immer sichtbaren „Hilfe“-Knopf (auch aus der Farblegende): Funktionen; Frame-Farben (aus `config/frame-colors.json`) und Grau-Liste; durchgeführte Prüfungen mit Quelle und **nicht durchgeführte Prüfungen** mit Grund (automatisch aus der Liste der Prüfschritte bzw. „nicht umgesetzt“); Guide-Stand; Schweregrade mit Symbolen.

## 8. Versionserkennung und Validierung (Grundstufe)

- **Versionserkennung** mit Begründung: Namespace, `version`-Attribut, `schemaLocation`, Kommentare, Dateiname, Struktur. Ergebnis `detected`, `ambiguous` oder `unknown`; das Wurzelattribut allein entscheidet nie (die Guide-Beispiele tragen teils `1.09`).
- **Passt die Datei nicht zum Guide-Stand** (z. B. 1.10-Lieferung): Ergebnis anzeigen, keine 2.0-Prüfung starten, generischer Explorer bleibt nutzbar.
- **XSD-Prüfung** (lxml) gegen die XSD des Guide-Stands; Fehler mit Datei, Zeile, Spalte, Markierung im XML. Geprüft am 31.10.2026: lxml lädt die NeTEx-2.1-XSD (`73b337e`) in **~17 s**, alle 22 Beispiele sind XSD-gültig. Deshalb XSD **einmal im Hintergrund beim Start laden** und wiederverwenden; Status in der Guide-Status-Box („XSD wird geladen …“).
- **Schematron:** `general_rules.sch` des Guides (4 allgemeine Regeln). Geprüft: meldet in 9 Beispielen 121 Verstösse, alle „`order`-Attribut nicht erlaubt“ (95× `StopPointInJourneyPattern`, 12× `PassengerStopAssignment`, 8× `TrainComponent`, 5× `NoticeAssignment`, 1× `DayTypeAssignment`); gute Testfälle.
- **Schweizer Kernregeln für den Fahrplan (~20):** selbst umgesetzt aus den Vorlagen `ServiceJourney.xml`, `ServiceJourneyPattern.xml`, `TimeDemandType.xml`: Pflichtelemente (z. B. `ServiceJourneyPatternRef`, `TimeDemandTypeRef`, `AvailabilityConditionRef`, `TrainNumberRef`; im Haltemuster `LineRef`, `DirectionType`, `ForBoarding`/`ForAlighting`; in Fahrzeiten `RunTime`), verbotene Elemente (z. B. `calls`, `passingTimes`, `LineRef`/`DirectionType` in der Fahrt) und erlaubte Werte (z. B. `ServiceAlteration` = `planned`). Jede Regel einzeln am Vorlagentext prüfen und mit Quelle (Vorlage, Stelle, Commit) versehen; unklare Regeln dem Benutzer vorlegen.
- Anzeige: „Schweizer Kernregeln für den Fahrplan geprüft; übrige Profilregeln noch nicht eingebunden“. Prüfungen als erweiterbare Liste von Prüfschritten; später kommen die übrigen Regeln über das Build-Werkzeug des Guides dazu.
- **Link zum Guide-Kapitel** über `A5_annex_index.md`, auf GitHub im exakt verwendeten Commit.
- Ergebnis heisst „geprüft gegen Entwurf <Commit>“, nie „gültig“.
- Bekannte erste Testfälle: `order`-Verstösse (z. B. Beispiel 22 mit 66 Meldungen), synthetische Fahrt mit `calls` (Kernregel). Hinweis: `TypeOfName` `offical` (Beispiele) ist vermutlich ein Tippfehler, aber kein Regelverstoss (freier Text) und wird nicht als Fehler gemeldet.

## 9. Sicherheit

- pyexpat ohne externe Entitäten und ohne Netzwerkzugriff; lxml mit `resolve_entities=False`, `no_network=True`.
- ZIP: Zip-Slip-Schutz, keine Symlinks; Standardgrenzen (in `config/settings.json` änderbar): 200 MB entpackt gesamt, 50 MB je Datei, 500 Dateien, Kompressionsrate 100:1.
- Server nur auf `127.0.0.1`, CORS nur für das lokale Frontend, keine freien Dateipfade über die API, keine Telemetrie, keine Cloud-Dienste.
- Über den Dialog geöffnete Dateien nur in `work/` (nicht versioniert); Aufräumen beim Schliessen des Datensatzes und beim Start.

## 10. Phasen und Abnahme

Nach jeder Phase: `scripts/check.py` grün, **Code-Review und Sicherheits-Review** mit behobenen Funden, **Hilfeseite und README nachführen**, Nachweis in `docs/test-report.md` (Prüfbefehl, Abdeckung, Reviews, Lücken), Commit. Fehler vor der nächsten Phase beheben. Lässt sich eine Phase nicht vollständig umsetzen, wird der funktionierende Teil mit genauer Beschreibung der Lücke geliefert, **kein vorgetäuschter Erfolg**; die Lücke wird dem Benutzer vorgelegt.

| Phase | Inhalt | Abnahme |
|---|---|---|
| **0 Grundgerüst** | Projektstruktur, Abhängigkeiten (uv, npm) mit Lockfiles, **Qualitätswerkzeuge** (ruff, mypy strict, pytest-cov, Biome, Vitest, pip-audit, npm audit), **`scripts/check.py`** und **Git-Hook** (`.githooks/pre-commit`), `config/`, Workspace-Datei, Guide-Erkennung (Pfad, Commit, XSD vorhanden, `guide-tested.json`), Mappingtabelle lesen, Start-Skripte, leere Oberfläche mit Sprachdateien; `docs/mapping.md` mit den bereits geprüften Ketten anlegen; synthetische Testdateien mit `fixtures/README.md` | `scripts/check.py` ist grün und wird vom Git-Hook vor jedem Commit ausgeführt; `scripts/test.py` läuft und schreibt `guide-tested.json`; mit dem geklonten Guide (`b7ac158`, XSD `73b337e`) startet die App lokal, zeigt den Guide-Commit an und liest die Mappingtabelle; fehlende XSD bzw. neuerer Stand werden gemeldet |
| **1 Einlesen und Objekt-Explorer** | pyexpat-Reader, Index, Frames, Pfade, Syntax-Diagnosen, Liste der Fahrten, einfache Objektsuche, Objektdetail, XML-Ansicht mit Markierung, Beispielauswahl mit Status pro Beispiel, Prüfsummen in `guide-tested.json` | **Alle Guide-Beispiele** laden ohne Absturz; ID-Suche zeigt Objekt mit Frame, Datei, Zeile/Spalte; Klick markiert exakt die Stelle |
| **2 Referenzen und Herkunft** | Referenzen inkl. `Extensions`, Auflösung über ID + Typ, Rückwärtsreferenzen, Herkunftsanzeige, Frame-Farben | Navigation vor/zurück; `Quay` und `ScheduledStopPoint` mit gleicher ID werden korrekt unterschieden; nicht auflösbare Referenzen als Diagnose |
| **3 Fahrtansicht CH 2.0** | Haltefolge mit Ein-/Aussteige-Eigenschaften, berechnete Zeiten mit Rechenkette, Mitternacht, Betriebstage, Zugnummer/Linie/Verkehrsmittel, Angebote inkl. `JourneyPart`, Hinweise, Stammdaten | Beispiel 01 zeigt die Halte in richtiger Reihenfolge und nachvollziehbar berechnete Zeiten mit Rechenkette (Abweichung zum Dateikommentar 10:53/10:54 geklärt und in `docs/assumptions.md` festgehalten); Beispiel 15 (`DepartureDayOffset` 1) und 21 (Kurswagen über Mitternacht) korrekt; Beispiel 08 zeigt Angebote auf Teilstrecken |
| **4 Eigene Dateien und Validierung** | Öffnen von XML/mehreren XML/ZIP, Versionserkennung, XSD + `general_rules.sch` + Kernregeln, Guide-Kapitel-Links | Eigene 2.0-Datei wird geprüft; 1.10-Datei wird erkannt und nicht irreführend geprüft; `order`-Verstösse der Beispiele erscheinen mit Stelle und Link zum Guide-Kapitel; eine synthetische Fahrt mit `calls` verletzt die Kernregel mit Quellenangabe |
| **5 Übergabe** | Hilfeseite, README, Start/Stopp, E2E-Test, Testbericht, bekannte Grenzen, Sprachdatei-Prüfung | Neue Person startet die App, lädt Beispiel 01, klickt einen Halt an und landet an der richtigen XML-Stelle, ohne Code zu ändern; Hilfeseite zeigt aktuelle Farben sowie durchgeführte und nicht durchgeführte Prüfungen |

## 11. Tests

- **Unit:** Guide-Erkennung (Commit aus `.git`, fehlende XSD, neuer als getestet), Namespaces, Positionen (Byte/Zeile/Spalte), Frame-Zuordnung, Pfadberechnung, Referenzauflösung (ID + Typ, doppelte IDs), Zeitberechnung inkl. Mitternacht und fehlender Summanden, `ValidDayBits`, Versionserkennung, Mappingtabelle (fehlende Spalte → Hinweis), Übersetzungsschlüssel vollständig.
- **Alle Guide-Beispiele:** parametrisierter Test lädt jedes Beispiel des aktiven Guide-Stands. Zwei Fälle getrennt: (1) **Absturz des Tools** bei einem Beispiel → Test schlägt fehl (Fehler im Tool). (2) **Fehler oder veralteter Stand im Beispiel** → kein Testfehler, sondern Eintrag im Testbericht und Ergebnis in `guide-tested.json`.
- **Fachliche Tests an bestimmten Beispielen** (01, 08, 15, 21): Hat sich die Prüfsumme des Beispiels seit dem letzten Test geändert und schlägt der Test fehl, meldet der Bericht „Beispiel geändert – Erwartung prüfen“ statt nur „fehlgeschlagen“; Ursache (Guide oder Tool) dem Benutzer vorlegen.
- **Hilfeseite aktuell:** Test schlägt fehl, wenn ein Prüfschritt, eine Frame-Farbe, ein Schweregrad oder eine Funktion (Liste in `app/core/features.py` bzw. gleichwertig) keinen Hilfetext in **beiden** Sprachdateien hat, oder wenn die Hilfeseite Farben/Prüfungen anders zeigt als `config/` und die Liste der Prüfschritte.
- **Synthetische Fixtures** (eigene, klein, als synthetisch gekennzeichnet, z. B. `ParticipantRef` `SYNTHETIC`; nie als echte Fahrplandaten ausgeben): Fahrt mit drei Halten, Fahrt über Mitternacht, fehlender Summand, nicht auflösbare Referenz, Referenz über Dateigrenzen, Referenz auf nicht geladene Datei (`external_or_unloaded`), doppelte ID, defektes XML, ZIP mit mehreren Dateien, 1.10-artige Datei, Fahrt mit `calls` (verletzt Kernregel).
- **Sicherheit:** XXE, Zip-Slip, ZIP-Grenzwerte, unzulässiger Pfad.
- **E2E (Playwright, ein Pfad):** Beispiel 01 laden → Fahrt öffnen → Halt anklicken → richtige XML-Stelle und Frame.
- **Keine festen Texte im Frontend-Code:** einfacher Prüftest.

## 12. Dokumentation

`README.md` (Installation von null inkl. **exakter Git-Befehle** zum Klonen des Guides und Holen der XSD, Start, Bedienung, Tests ausführen, bekannte Grenzen, **Windows-Testanleitung** für den ersten Test am Windows-PC), `fixtures/README.md` (Herkunft der synthetischen Daten, Weitergabe erlaubt), `docs/mapping.md` (jede fachliche Regel mit Guide-Beleg), `docs/api.md`, `docs/assumptions.md` (Annahmen, Widersprüche im Guide), `docs/test-report.md`. Entscheidungen weiterhin in `docs/decisions.md`.

## 13. Arbeitsweise für die Umsetzung

Für eine neue Sitzung, die diesen Plan umsetzt:

1. Zuerst lesen: [CLAUDE.md](CLAUDE.md), [docs/engineering-guidelines.md](docs/engineering-guidelines.md), [docs/decisions.md](docs/decisions.md), diesen Plan, [docs/research/guide-2.0.md](docs/research/guide-2.0.md), [docs/open-points.md](docs/open-points.md).
2. Prüfen, ob der Guide-Klon vorhanden ist (`../netexRealisationGuideSwitzerland`, Branch `next`, XSD-Submodul). Fehlt er: Benutzer auf die Befehle im README hinweisen, nicht selbst klonen.
3. Phasen 0–5 der Reihe nach umsetzen. Nach jeder Phase: `scripts/check.py` grün, Code-Review und Sicherheits-Review, Nachweis in `docs/test-report.md`, Commit, kurze Rückmeldung an den Benutzer (was fertig ist, was offen ist). `--no-verify` nie verwenden.
4. **Anhalten und den Benutzer fragen** bei: Elementen, deren Einordnung in Grau unklar ist, unklaren Kernregeln, jeder Unklarheit oder jedem Widerspruch (Plan, Entscheidungen, Guide, Daten), jeder Anforderung mit unerwartet hohem Aufwand. Fragen einzeln stellen.
5. **Jede Änderung an Funktionen, Farben oder Prüfungen führt die Hilfeseite im selben Commit nach** (Regel in CLAUDE.md, abgesichert durch Test).
6. Neue Entscheidungen in `docs/decisions.md`, fachliche Belege in `docs/mapping.md`, Annahmen und Widersprüche im Guide in `docs/assumptions.md`.
7. Nichts auf GitHub oder andere Server hochladen; keine Lieferdaten aus `../netex-files/` in den Kontext laden.

## 14. Während der Planung geklärte Fragen

1. Referenzgraph → keine Graph-Bibliothek; Frame-Farben, Herkunftskette als Kästchen, farbige Referenzliste (Abschnitt 7).
2. Index und Import → Index nur im Arbeitsspeicher, Datei wird beim Öffnen direkt eingelesen; keine Datenbankdatei, kein Hintergrundprozess.
3. Profilregeln → XSD + `general_rules.sch` + ~20 selbst umgesetzte Kernregeln für den Fahrplan; übrige ~330 Regeln später über das Werkzeug des Guides; kein Halt nach Phase 3 (Abschnitt 8).
4. Plattformen → Windows bald nötig und wichtiger als die Webversion; Windows-Test von Hand, sobald ein Windows-PC verfügbar ist.
5. Guide-Bezug → Git-Klon durch den Benutzer statt Download-Skript; Workspace-Datei; eigene Dateien nur über den „Datei öffnen“-Dialog.
6. Hilfeseite → Funktionen, Farben, durchgeführte und nicht durchgeführte Prüfungen, automatisch aus den Daten; wird bei jeder Änderung nachgeführt (Abschnitt 7, 11, 13).
7. Teilweise aktualisierte Guide-Beispiele → Status pro Beispiel, Prüfsummen in `guide-tested.json`, Tests trennen Tool-Absturz von Beispielfehlern (Abschnitte 4, 7, 11).
8. Codequalität → verbindliche Regeln in `docs/engineering-guidelines.md`, erzwungen durch `scripts/check.py` und Git-Hook, Reviews vor jedem Phasenabschluss.

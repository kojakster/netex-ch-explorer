# CH-Profil 2.0 (Entwurf, NeTEx 2.1): Rechercheergebnisse

Ursprüngliche Erhebung: 30.10.2026. Lokaler Guide-Stand und bestehende Belege zuletzt am 06.11.2026 gegen `5faccdec` geprüft. Historische Messungen nennen ihren damaligen Stand ausdrücklich; Nachweis des aktuellen Updates am Ende dieses Dokuments.

## Quellen

- Guide (Webseite): https://opentdatach.github.io/netexRealisationGuideSwitzerland/main/index.html. Release Candidate 1 vom 07.09.2026, Release geplant 2026-11. Die Seite `…/main/…` entspricht möglicherweise einem älteren Stand.
- Repository: https://github.com/openTdataCH/netexRealisationGuideSwitzerland
  - Lokaler Branch `next` = `5faccdec` (Commit vom 04.11.2026, geprüft am 06.11.2026; vorher getestet `d0a8e6d`, davor `b7ac158`). Die ursprüngliche Erhebung nennt `main` = `3b5c0d2`; dieser Branch und die Online-Veröffentlichung wurden für das lokale Update nicht neu geprüft.
  - Keine Releases; Lizenz nicht angegeben; Kontakt info.fachbus@sbb.ch.
- Echte Lieferungen im Profil 2.0 gibt es noch nicht, weil NeTEx 2.1 selbst noch in Entwicklung ist. Auch das SKI+-Handout vom 25.03.2026 nennt keinen Termin: https://www.oev-info.ch/sites/default/files/2026-04/2026_03_25_Handout_NeTEx.pdf
- Weitere CH-Profildokumente (für spätere Adapter, nicht geprüft): Profil 1.0.0 https://www.oev-info.ch/sites/default/files/2024-05/NeTEx_Core-Realisation_Guide_TP_Suisse-v1.00.pdf

## Bereitgestellte Artefakte (Branch `next`, ~23 MB ohne XSD)

| Pfad | Inhalt | Verwendung im Explorer |
|---|---|---|
| `src/examples/*.xml` | 22 Beispiele (4–56 KB) + `README.md` | Hauptdaten für Fahrtansicht, Tests und Abnahme |
| `src/templates/*.xml` | 76 Templates (Stand `5faccdec`), darunter Vorlagen pro Element (z. B. `ServiceJourney.xml`, `TimeDemandType.xml`), Datei-Skelette `ch-profile_SINGLE_FILE`, `_NETWORK_OFFER`, `_SITE_OFFER`, `_INTERCHANGE` und einige `*_deprecated.xml` | Referenz für erlaubte Elemente pro Objekttyp; Erkennung des Dateityps |
| `src/schematron_rules/general_rules.sch` | Allgemeine Schematron-Regeln (1,7 KB). Weitere Schematrons erzeugt der Build aus den Templates (Ausgabe `site/`, nicht im Repo) | Profilprüfung |
| `xsd` (Submodul) | NeTEx-CEN, Branch `v2.1-wip`, gepinnt auf `73b337e` | XSD-Prüfung gegen Entwurf |
| `src/*.md` | Kapitel 01–09, Use Cases uc01–uc13 ff., Annexe A1–A6 (A6: Migration 1.0 → 2.0, „work in progress“) | Fachliche Belege für `docs/mapping.md` |
| `src/media/Mappingtabellen_NeTEx_v2.0.xlsx` | Mapping-Tabellen (Notices, ProductCategory, Facilities) | Codelisten/Anzeigetexte |
| `tools/`, `pyproject.toml` | Python-Build-Tools des Guides | Nur lesen; nicht ohne Prüfung ausführen |

## Lieferstruktur laut Guide (`src/02_files.md`)

- Dateitypen:
  - **`NETWORK_OFFER`**: Linien, Routen, Fahrpläne; ggf. mehrere Dateien.
  - **`INTERCHANGE`**: Anschlüsse, Flügelungen, Durchbindungen.
  - **`SITE_OFFER`**: Haltestellen, Perrons, Umsteigezeiten, Barrierefreiheit (`02_files.md` Z. 76). Bis `b7ac158` hiess der Typ im Text `STOP_OFFER` (Inkonsistenz); mit `d0a8e6d` einheitlich `SITE_OFFER`.
  - `SINGLE_FILE`: nur als Template vorhanden.
- SKI liefert ein SITE_OFFER, mehrere NETWORK_OFFER, ein INTERCHANGES-XML und eine README-Datei mit dem Inhalt jeder XML-Datei.
- ZIP-Name, Beispiel: `TEST_NETEX_TT_2.0_CHE_SKI_2026_OEV-SCHWEIZ_202602010402.zip`.
- INTERCHANGE ist laut Guide nur dann XSD-valide, wenn `versionRef` statt `version` verwendet wird.

## Datenmodell der Beispiele

- **Haltefolge und Zeiten:** Alle 22 Beispiele verwenden **`ServiceJourneyPatternRef` → `StopPointInJourneyPattern`** sowie **`DepartureTime` + `TimeDemandTypeRef`** (`JourneyRunTime`/`JourneyWaitTime` je `TimingLink`). Kein Beispiel nutzt `TimetabledPassingTime` oder `Call`. Die Templates `TimetabledPassingTime_deprecated.xml` und `ServiceJourney_PassingTime_deprecated.xml` sind als veraltet markiert.
- **Widerspruch Dokumentation/Dateien:** `examples/README.md` erwähnt noch „PassingTimes“ (Beispiele 02, 07). Massgebend sind die Dateien; den Widerspruch in `docs/assumptions.md` festhalten.
- **Zeiten an den Halten werden berechnet.** Die Herkunftsanzeige muss die Rechenkette als „abgeleitet“ zeigen, jeden Summanden mit eigener Quelle.
- Alle Frames in einer Datei; IDs mit `version="1"`, teils lokale IDs (`sjp1`, `tdt-1`).
- **Dieselbe ID für verschiedene Typen:** `ch:1:sloid:7483:0:90840` ist `Quay` **und** `ScheduledStopPoint`. Referenzen deshalb immer über (ID, erwarteter Typ) auflösen; den Typ aus dem Namen des Ref-Elements bzw. aus `nameOfRefClass` ableiten.
- **Wurzelattribut `version`:** 19 Beispiele `"2.1"`, 2 noch `"1.09"` (u. a. 01), 08 weicht ab. `schemaLocation` ist relativ (`../../xsd/xsd/NeTEx_publication.xsd`). Das Wurzelattribut allein taugt nicht zur Versionserkennung.
- **Fälle, die die Fahrtansicht abdecken muss** (je ein Beispiel):
  - Facilities nur auf Teilstrecken bzw. an einzelnen Tagen (08, `JourneyPart`)
  - Flügelzug (06, 13)
  - Durchbindung (07)
  - Kurswagen (21; Beispiel 19 seit `d0a8e6d` entfernt)
  - Formation (20)
  - Taktlinie (12)
  - Bedarfsverkehr DRT (04, 05)
  - Zieländerung (10)
  - Zugnummernwechsel (11)
  - Teillinien/Subunternehmer (22)
  - Perron/sloid-Problem (09)

## Fahrten über Mitternacht

Geprüft am Stand `b7ac158`; Zeilenangaben und Regeln zuletzt am 06.11.2026 gegen `5faccdec` geprüft (gegenüber `d0a8e6d` unverändert). Neu in `d0a8e6d`: Sonderfall Zeitumstellung in `08_timetable.md` (zweite Fahrt in der doppelten Stunde, `DepartureTime` in UTC, z. B. `02:33:00Z`), siehe [mapping.md](../mapping.md) Z8, Z9.

| # | Regel | Quelle |
|---|---|---|
| 1 | Zeiten sind Ortszeit `hh:mm:ss` (24 h) ohne Zeitzone/UTC-Offset, damit Fahrten nicht für Sommer- und Winterzeit doppelt geführt werden müssen. | `src/08_timetable.md`, `src/03_xml_modelling.md` („Time Formatting and Journey after Midnight“) |
| 2 | Betriebstage einer Fahrt kommen aus `AvailabilityConditionRef` → `AvailabilityCondition`/`ValidDayBits`, nicht aus `DayType` (`DayType`/`DayTypeAssignment` nur für Feiertage). `OperatingDay`/`OperatingPeriod` werden im CH-Profil nicht verwendet. Ein einzelner Tag wird als `FromDate` `…T00:00:00` / `ToDate` `…T23:59:59` beschrieben. | `src/08_timetable.md` („Day Governance“), `src/07_service_calendars.md`, `src/03_xml_modelling.md`, `src/A4_annex_glossary.md` |
| 3 | Fall 1: Abfahrt nach Mitternacht, Fahrt gehört aber zum Vortag → `DepartureDayOffset` = `1` (Beispiel im Text: S1 um 00:11). | `src/uc10_midnight_passing.md` |
| 4 | `DepartureDayOffset` ist optional („0 for current operating day. Could also be negative.“). Negativ „sehr selten“, z. B. wenn ein Zug am Vortag bei einem anderen Betreiber startet und der Betriebstag erhalten bleiben soll. | `src/templates/ServiceJourney.xml`, `src/08_timetable.md` |
| 5 | Fall 2: Mitternacht wird während der Fahrt überschritten → kein eigenes Element. `TimeDemandType`/`TimingLink` enthalten nur relative Dauern; der Tageswechsel folgt implizit aus dem Aufsummieren von `DepartureTime` und `RunTime`/`WaitTime`. | `src/uc10_midnight_passing.md`, `src/03_xml_modelling.md` |
| 6 | `JourneyPart` trägt den Tag ausdrücklich: `StartTime`/`StartTimeDayOffset`, `EndTime`/`EndTimeDayOffset`. | `src/uc05_journey_parts.md`, Beispiele 08, 21 |

Vorkommen in den Beispielen:

- `DepartureDayOffset`: in 12 Beispielen gesetzt, fast immer `0`. Einziger Wert `1`: **Beispiel 15** (`DepartureTime` `04:34:00`, Zeile 475–476), die Fahrt gehört also zum vorherigen Betriebstag.
- **Beispiel 21** (Kurswagen Zürich–Bremen, `ServiceJourney` `ch:1:ServiceJourney:KW37`):
  - `JourneyPart` 2: 23:40 → 06:12 mit `EndTimeDayOffset` `1`.
  - `JourneyPart` 3: 06:44 mit `StartTimeDayOffset` `1`.
  - Die anschliessende `ServiceJourney` 2746 hat `DepartureTime` 06:44 mit `DepartureDayOffset` `0`. Das ist konsistent, wenn ihre Betriebstage um einen Tag gegenüber KW37 verschoben sind. Prüfbar ist das nur über die `ValidDayBits`; bei der Umsetzung kontrollieren.
- Templates mit `DayOffset`-Elementen: `ServiceJourney`, `TemplateServiceJourney`, `JourneyPart`, `CheckConstraint`, `CompoundTrain`, `Destination`, `Train`, `TrainComponent`, `TrainElement`.

## Codes in den Beispielen und Mappingtabelle

Geprüft am Stand `b7ac158` (XSD `73b337e`); Mappingtabelle in `d0a8e6d` und `5faccdec` unverändert.

- **Häufigkeit:** In den 22 Beispielen stehen an 360 Stellen reine Codes, etwa 48 verschiedene in rund 30 Elementtypen. Nicht mitgezählt sind Platzhalter und Freitext wie `blabla`, `de`, `x`, `running`.
- **Schweiz-spezifisch gepflegte Werte:** Sie kommen in Blättern der Mappingtabelle vor. Beispiele: `TransportMode`/Submodes (`VMArt->NeTEx`), Facilities wie `bistro`, `lowFloor`, `freeWifi`, `firstClass` (`Angebote`, `Facilities_gemappt`), `StopPlaceType`, `QuayType`, `StopUse`, `LineType`, `Weighting` (`Weightening`). Wortübereinstimmung bei 200 der 360 Stellen. Ob die Tabelle den Wert jeweils auch erklärt, ist erst beim gezielten Auslesen zu bestätigen.
- **Allgemeine NeTEx-Werte ohne Stammdaten:** `ServiceAlteration` `planned` (39), `DirectionType` `outbound`/`inbound` (38), `NameType` `alias` (24), `ThroughAccess`, `TrainElementType`, Buchungswerte (`advanceOnly`, `mobileApp`), `AccessibilityToolList` u. a.
- **NeTEx-XSD als Quelle für Bedeutungen ungeeignet:** Nur 836 von 8955 Aufzählungswerten haben eine `xsd:documentation`, oft ohne Aussage (`bistro` → „pti23_26“, `country` → „+v1.1“). `inbound`, `outbound`, `planned` und `alias` haben keine.
- **Auffälligkeiten in den Beispielen:**
  - `TypeOfName` `offical` (18-mal, vermutlich Tippfehler für „official“; `TypeOfName` ist keine Aufzählung, die XSD meldet das also nicht).
  - `Name`/`Description` `blabla` als Platzhalter.

### Lesbarkeit der Mappingtabelle

Untersucht wurden die Blätter, die Codes erklären (`VMArt->NeTEx`, `Angebote`, `Facilities_gemappt`, `StopPlaceType`, `QuayType`, `StopUse`, `LineType`, `Weightening`).

- **Aufbau:** Jedes Blatt ist eine Tabelle mit 1–5 Titelzeilen und danach einer **Kopfzeile mit Spaltennamen**. Die Kopfzeile liegt je nach Blatt in Zeile 2, 3 oder 6. Danach folgt pro Zeile ein Wert, über eine Code-Spalte identifizierbar (z. B. `Abk`, `Value`, `Facility Value`, `Value for LineType`). Zusammengeführte Zellen gibt es nur in Titelzeilen (`Angebote` B1:C1/E1:F1, `LineType` A4:F4 u. a.).
- **Farben tragen Bedeutung:** Blatt `Legend`: grün = „new value“, orange = „no longer used“. Viele Zellen sind farbig, besonders in `Angebote` und `LineType`.
- **Datenqualität:** Die Tabelle hat eigene Schreibweisen und Tippfehler, z. B. Facility Value `Bar` (gross) oder „Abfahrstszeiten“. Das Tool zeigt die Werte so an, wie sie dort stehen.

## XSD- und Schematron-Prüfung der Beispiele (31.10.2026)

Mit lxml lokal geprüft (`b7ac158`, XSD `73b337e`; die Angaben zu `order` gelten nur für diesen Stand, seit `d0a8e6d` enthalten die Beispiele kein `order` mehr und ergeben 0 Verstösse; alle Beispiele bleiben XSD-gültig):

- Die NeTEx-2.1-XSD lädt in ~17 s, ist also beim Start einmal im Hintergrund zu laden.
- **Alle 22 Beispiele sind XSD-gültig.** Verschachtelte `<Text lang="…">` innerhalb von `<Text>`/`<Name>` (Beispiel 05 Zeile 399, Beispiel 16 Zeile 64) sind die NeTEx-2.x-Form für Übersetzungen, kein Fehler.
- `general_rules.sch`: 121 Verstösse in 9 Beispielen, alle „The order attribute is not allowed“ (95× `StopPointInJourneyPattern`, 12× `PassengerStopAssignment`, 8× `TrainComponent`, 5× `NoticeAssignment`, 1× `DayTypeAssignment`). Laut `03_xml_modelling.md` ergibt sich die Reihenfolge aus der XML-Reihenfolge.

## Guide-Update 5faccdec (06.11.2026)

Lokal geprüft: `d0a8e6dff2ebecfb47195b5f9aedd79a899d8c33` → `5faccdec4e3065f0774b832a785a935fb00539ed`. Zwei Commits: `6587658a436571811945c63dc5f198e9da0cdccc` („Refactoring with additional tables“) und der Merge `5faccdec` (PR #290). Keine Guide-Datei geändert oder kopiert, keine Guide-Werkzeuge ausgeführt.

| Datei / Zeilen in `5faccdec` | Änderung und Bedeutung für den Explorer |
|---|---|
| `src/05_stops.md` Z. 14–16, 288–343 | Neue Kapitel zu `StopPlaceEntrance` (Bezugspunkt der Barrierefreiheitsbewertung), `AssistanceService` (Hilfsdienste und Verfügbarkeit) und `AssistanceBookingService` (Kontakt/Buchung). Bestehender Kapitelinhalt ab der Inhaltsliste um 3 Zeilen verschoben. Keine bestehende Fahrplanregel geändert. |
| `src/templates/StopPlace.xml` Z. 161–162, 172–175, 188–219 | Zwei Kommentare als `ch-note` markiert, Assistance-Kommentare ergänzt, optionaler `AssistanceBookingService` unter `localServices` ergänzt. Danach verschieben sich Zeilen um insgesamt 34 (z. B. `StopPlaceType` 187 → 221). `Name`, `Quay`-Zuordnung und `PassengerStopAssignment` werden dadurch nicht neu gedeutet. |
| `src/templates/StopPlaceEntrance.xml` Z. 85–129 (neu) | Eigene Vorlage: Barrierefreiheitsbewertung, `LevelRef`, Eingangsmerkmale. Enthält ausdrücklich offene Diskussionsvermerke. |
| `src/templates/AssistanceService.xml` Z. 93–112 (neu) | Eigene Vorlage für Hilfsdienste, Verfügbarkeit und Hilfsmittel; `AssistanceAvailability` hier `expected`, in `StopPlace.xml` Z. 183 weiterhin `optional`. |
| `src/templates/AssistanceBookingService.xml` Z. 97–138 (neu) | Optionale Buchungsangaben mit Kontakt, Verkehrsmittel und zeitlich eingeschränkten Hinweisen. |

**Auswirkung:** Keine Anpassung des Anwendungscodes oder der 30 Kernregeln erforderlich. Die Haltestellen-Zuordnung folgt weiterhin `PassengerStopAssignment` → `StopPlaceRef`/`QuayRef`, der Name kommt aus dem referenzierten Objekt (H4). Entrance-/Assistance-Inhalte bleiben im generischen Objekt-Explorer und XML sichtbar. Die bestehende Grau-Liste erfasst `entrances` und `localServices` samt Inhalt; sie wird nicht erweitert. Die neuen Profilangaben gehören zu den noch nicht eingebundenen übrigen Profilregeln. Die offenen Angaben werden dokumentiert ([assumptions.md](../assumptions.md) Nr. 13), ohne daraus Prüfregeln abzuleiten.

**Belege:** Keine der vor diesem Update konkret zitierten Guide-Quelldateien in `mapping.md`, `core-rules.md`, `assumptions.md` und diesem Dokument ist im Diff geändert. Bestehende Zeilenverweise bleiben deshalb unverändert; die neu ergänzten Belege oben beziehen sich ausdrücklich auf `5faccdec`.

**Unveränderte Prüfgrundlagen:** `git diff --exit-code d0a8e6d 5faccdec -- src/examples src/media src/schematron_rules xsd` ist leer. Identische Git-Tree-IDs für Beispiele (`1a7c309f948e837aa598afaf29dee20c49189cfa`), Medien (`1d52aca6e5b33b469143a8d81a9d603d1d523083`) und Schematron (`9deb3645e33b813b8f2cfd7a4b5e78bc7a18ee65`). XSD-Gitlink und ausgecheckter Submodul-Commit sind `73b337e22ceed7905a1be14e4e506f1afa359b54`. Mappingtabelle: SHA-256 `c4db0b16ede1d2dbae5b716f0bbc6dd21a885c41f54e8b1232339e382d8231d1`.

**Erneute Beispielprüfung:** Alle 22 SHA-256-Werte und Ergebnisse stimmen mit dem bisherigen `guide-tested.json` überein: 20 ohne Meldungen, Beispiel 17 mit 7 Hinweisen (3 Rumpf-Fahrten, 4 externe/nicht geladene Referenzen), Beispiel 23 mit einem Fehler (`ParentSiteRef` auf `ch:1:sloid:169`, Ziel fehlt). Kein `order`-Verstoss, keine Abweichung zur bisherigen Erwartung. Vollständiger Nachweis: [test-report.md](../test-report.md#guide-update-5faccdec-06112026).

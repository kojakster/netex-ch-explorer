# Fachliche Abbildung CH 2.0: Belege im Guide

Jede fachliche Regel des Adapters „CH 2.0“ ist hier mit Guide-Datei, Stelle und Commit belegt. Grundlage: Guide-Klon `netexRealisationGuideSwitzerland`, Branch `next`, Commit **`b7ac158`** (XSD `73b337e`). Pfade relativ zum Guide-Klon. Zeilenangaben gelten für diesen Commit.

**Stand:** Phase 0 (31.10.2026). Erfasst sind die Ketten, die bei der Planung bereits am Guide geprüft wurden ([research/guide-2.0.md](research/guide-2.0.md)). Umgesetzt werden sie ab Phase 3. Jede Regel wird bei der Umsetzung erneut am Text geprüft und hier nachgeführt.

Status: **belegt** = Guide-Text eindeutig; **offen** = Widerspruch oder Lücke, wird dem Benutzer vorgelegt.

## Haltefolge

| # | Regel | Beleg | Status |
|---|---|---|---|
| H1 | Eine `ServiceJourney` verweist auf genau ein `ServiceJourneyPattern` (`ServiceJourneyPatternRef`); dessen Haltefolge ist massgebend. | `src/08_timetable.md` Z. 80 („Consistency“), Z. 84; `src/templates/ServiceJourney.xml` Z. 99–102 | belegt |
| H2 | Reihenfolge der Halte = **Reihenfolge der `StopPointInJourneyPattern` im XML** (`pointsInSequence`). | `src/03_xml_modelling.md` Z. 236–237 („Ordering of Elements“) | belegt |
| H3 | Das Attribut `order` ist nicht erlaubt. Steht es trotzdem da und weicht ab, entsteht ein Hinweis; massgebend bleibt die XML-Reihenfolge. | `src/schematron_rules/general_rules.sch` Z. 30–34 (Regel d) | belegt |
| H4 | Kette zum Halt: `StopPointInJourneyPattern/ScheduledStopPointRef` → `ScheduledStopPoint` → `PassengerStopAssignment` (`ScheduledStopPointRef`) → `StopPlaceRef`/`QuayRef` → `StopPlace`/`Quay`. | `src/templates/PassengerStopAssignment.xml` Z. 14–24 | belegt |
| H5 | `ScheduledStopPointRef` fehlt in einer `PassengerStopAssignment` nur bei `passengerBoardingPositionAssignments`. | `src/templates/PassengerStopAssignment.xml` Z. 16 | belegt |
| H6 | `Quay` und `ScheduledStopPoint` können dieselbe ID haben; Auflösung deshalb über (ID, erwarteter Typ). | Beispiel `src/examples/01_NeTEx_Spiez_Interlaken_Ost.xml` (`ch:1:sloid:7483:0:90840` als `Quay` und `ScheduledStopPoint`) | belegt |
| H7 | In `NETWORK_OFFER`-Dateien fehlen Haltestellen (Lieferanten senden `NETWORK_OFFER` und `INTERCHANGE`; `STOP_OFFER` nur für Daten, die nicht in ATLAS stehen); Verweise darauf sind `external_or_unloaded`, kein Fehler. | `src/02_files.md` Z. 142; Beispiel 18 ohne `SiteFrame` | belegt |

## Halt-Eigenschaften

| # | Regel | Beleg | Status |
|---|---|---|---|
| E1 | `ForAlighting` und `ForBoarding` sind Pflicht je `StopPointInJourneyPattern`; `RequestStop` und `StopUse` optional. | `src/templates/ServiceJourneyPattern.xml` Z. 29–36 | belegt |
| E2 | `StopUse`: alle Werte möglich; `passthrough` für Durchfahrt. Bedeutungen aus der Mappingtabelle, Blatt `StopUse`. | `src/templates/ServiceJourneyPattern.xml` Z. 36 (ch-note) | belegt |

## Linie und Richtung

| # | Regel | Beleg | Status |
|---|---|---|---|
| L1 | Die Linie steht im `ServiceJourneyPattern` (`RouteView/LineRef`), nicht in der `ServiceJourney`. | `src/08_timetable.md` Z. 88; `src/templates/ServiceJourneyPattern.xml` Z. 17; `src/templates/ServiceJourney.xml` Z. 112–115 | belegt |
| L2 | `DirectionType` ist im `ServiceJourneyPattern` Pflicht und in der `ServiceJourney` verboten. | `src/templates/ServiceJourneyPattern.xml` Z. 21; `src/templates/ServiceJourney.xml` Z. 116 | belegt |

## Zeiten

| # | Regel | Beleg | Status |
|---|---|---|---|
| Z1 | Genau ein `TimeDemandType` je `ServiceJourney` (`TimeDemandTypeRef`). | `src/08_timetable.md` Z. 84; `src/templates/ServiceJourney.xml` Z. 103–106 | belegt |
| Z2 | `ServiceJourney/DepartureTime` ist die Abfahrt am ersten `StopPointInJourneyPattern`. | `src/08_timetable.md` Z. 95 | belegt |
| Z3 | Ankunft am nächsten Halt = vorherige Abfahrt + `JourneyRunTime/RunTime` des `TimingLink` zwischen den beiden Halten. | `src/08_timetable.md` Z. 96; `src/templates/TimeDemandType.xml` Z. 64–71 | belegt |
| Z4 | **Welcher `TimingLink`:** Laut Guide-Text über `StopPointInJourneyPattern/OnwardTimingLinkRef`. Beispiel 01 hat **kein** `OnwardTimingLinkRef`; dort ergibt sich der `TimingLink` nur über `FromPointRef`/`ToPointRef` (`src/templates/TimingLink.xml` Z. 56–65). `OnwardTimingLinkRef` kommt nur in den Beispielen 06, 09, 13 und 18 vor. | `src/08_timetable.md` Z. 96 | **offen** (vor Phase 3 dem Benutzer vorlegen) |
| Z5 | Abfahrt an einem Halt = Ankunft + `JourneyWaitTime/WaitTime` dieses `ScheduledStopPoint`. Bei mehrfachem Besuch desselben Halts gilt `StopPointInJourneyPatternRef` vor `ScheduledStopPointRef`. | `src/08_timetable.md` Z. 97; `src/templates/TimeDemandType.xml` Z. 76–84 | belegt |
| Z6 | Zeiten sind Ortszeit `hh:mm:ss` ohne Zeitzone. | `src/03_xml_modelling.md` Z. 228–233; `src/08_timetable.md` Z. 87 | belegt |
| Z7 | Fehlt ein Summand, ist die Zeit „nicht berechenbar“ (kein Standardwert). | Projektregel „Nichts erfinden“ ([UMSETZUNGSPLAN.md](../UMSETZUNGSPLAN.md) Abschnitt 3) | belegt |

## Mitternacht

| # | Regel | Beleg | Status |
|---|---|---|---|
| M1 | Fahrt beginnt nach Mitternacht, gehört aber zum Vortag: `DepartureDayOffset` = 1. | `src/uc10_midnight_passing.md` Z. 3–9 | belegt |
| M2 | `DepartureDayOffset` ist optional; fehlt es, gilt 0 (als Standardwert gekennzeichnet). Negativ nur sehr selten. | `src/templates/ServiceJourney.xml` Z. 94–98; `src/08_timetable.md` Z. 90 | belegt |
| M3 | Tageswechsel während der Fahrt hat kein eigenes Element; er folgt aus dem Aufsummieren von `DepartureTime` und `RunTime`/`WaitTime`. | `src/uc10_midnight_passing.md` Z. 11 ff.; `src/03_xml_modelling.md` Z. 232–233 | belegt |
| M4 | `JourneyPart` trägt den Tag ausdrücklich: `StartTime`/`StartTimeDayOffset`, `EndTime`/`EndTimeDayOffset`. | `src/templates/JourneyPart.xml` Z. 82–85 | belegt |

## Betriebstage

| # | Regel | Beleg | Status |
|---|---|---|---|
| B1 | Betriebstage über `AvailabilityConditionRef` → `AvailabilityCondition` (`FromDate`, `ToDate`, `ValidDayBits`), nicht über `DayType`. | `src/08_timetable.md` Z. 81 („Day Governance“) | belegt |
| B2 | `ValidDayBits`: genau ein Bit je Kalendertag des Zeitraums, `1` = gültig. | `src/07_service_calendars.md` Z. 111 | belegt |
| B3 | Nur ein `AvailabilityConditionRef` je `ServiceJourney`. | `src/templates/ServiceJourney.xml` Z. 16–19 | belegt |
| B4 | `DayType`/`DayTypeAssignment` nur für nationale Feiertage. | `src/07_service_calendars.md` Z. 165, 217, 232 | belegt |
| B5 | Ein einzelner Tag wird als `…T00:00:00` bis `…T23:59:59` beschrieben. | `src/03_xml_modelling.md` Z. 220–225 | belegt |

## Fahrtbezeichnung

| # | Regel | Beleg | Status |
|---|---|---|---|
| F1 | Zugnummer über `trainNumbers/TrainNumberRef` → `TrainNumber` (`ForAdvertisement`). | `src/templates/ServiceJourney.xml` Z. 119–121; Beispiel 01 | belegt |
| F2 | Schweizer Fahrt-ID (sjyid) in `privateCodes/PrivateCode` mit `type="sjyid"`, nicht in `keyList`. | `src/08_timetable.md` Z. 89; `src/templates/ServiceJourney.xml` Z. 23, 37–41 | belegt |

## Noch nicht belegt (folgt mit der Umsetzung)

Verkehrsmittel und Produkt (`TransportMode`/Submode, `TypeOfProductCategoryRef`), Angebote (`ServiceFacilitySet`, `JourneyPart` auf Teilstrecken, Beispiel 08) und Hinweise (`NoticeAssignment` → `Notice`) werden in Phase 3 am Guide belegt und hier ergänzt.

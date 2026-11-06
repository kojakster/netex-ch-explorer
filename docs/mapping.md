# Fachliche Abbildung CH 2.0: Belege im Guide

Jede fachliche Regel des Adapters „CH 2.0“ ist hier mit Guide-Datei, Stelle und Commit belegt. Grundlage: Guide-Klon `netexRealisationGuideSwitzerland`, Branch `next`, Commit **`5faccdec`** (XSD `73b337e`; zuvor `d0a8e6d`, alle bestehenden Quelldateien und Zeilenangaben am 06.11.2026 gegen `5faccdec` geprüft, unverändert). Pfade relativ zum Guide-Klon. Zeilenangaben gelten für diesen Commit; historische Angaben nennen ihren damaligen Stand ausdrücklich.

Das Update `d0a8e6d` → `5faccdec` ergänzt Eingänge und Hilfsdienste im Haltestellenmodell. Die Zuordnung zum Halt (H4) und die Fahrplanregeln ändern sich dadurch nicht. Die neuen Profilangaben zu `StopPlaceEntrance`, `AssistanceService` und `AssistanceBookingService` gehören weiterhin zu den nicht eingebundenen übrigen Profilregeln; Inhalte bleiben im Objekt-Explorer und XML sichtbar. Belege und Grenzen: [research/guide-2.0.md](research/guide-2.0.md#guide-update-5faccdec-06112026).

**Stand:** Phase 3 (31.10.2026). Die Regeln H, E, L, Z, M, B, F, V, A, N und P sind in `app/core/projection/` umgesetzt (`journeys.py`, `journey_view.py`, `timing.py`, `calendar.py`, `offers.py`, `notices.py`, `master_data.py`) und bei der Umsetzung erneut am Guide-Text geprüft. Annahmen und Widersprüche im Guide stehen in [assumptions.md](assumptions.md).

Status: **belegt** = Guide-Text eindeutig; **Auslegung** = der Guide-Text sagt es nicht ausdrücklich, die Beispiele oder eine Folgerung stützen es (steht dann auch in [assumptions.md](assumptions.md)); **offen** = Widerspruch oder Lücke, wird dem Benutzer vorgelegt ([open-points.md](open-points.md)).

## Haltefolge

| # | Regel | Beleg | Status |
|---|---|---|---|
| H1 | Eine `ServiceJourney` verweist auf genau ein `ServiceJourneyPattern` (`ServiceJourneyPatternRef`); dessen Haltefolge ist massgebend. | `src/08_timetable.md` Z. 80 („Consistency“), Z. 84; `src/templates/ServiceJourney.xml` Z. 99–102 | belegt |
| H2 | Reihenfolge der Halte = **Reihenfolge der `StopPointInJourneyPattern` im XML** (`pointsInSequence`). | `src/03_xml_modelling.md` Z. 240–241 („Ordering of Elements“) | belegt |
| H3 | Das Attribut `order` ist nicht erlaubt. Steht es trotzdem da und weicht ab, entsteht ein Hinweis; massgebend bleibt die XML-Reihenfolge. | `src/schematron_rules/general_rules.sch` Z. 30–34 (Regel d) | belegt |
| H4 | Kette zum Halt: `StopPointInJourneyPattern/ScheduledStopPointRef` → `ScheduledStopPoint` → `PassengerStopAssignment` (`ScheduledStopPointRef`) → `StopPlaceRef`/`QuayRef` → `StopPlace`/`Quay`. | `src/templates/PassengerStopAssignment.xml` Z. 14–24 | belegt |
| H5 | `ScheduledStopPointRef` fehlt in einer `PassengerStopAssignment` nur bei `passengerBoardingPositionAssignments`. | `src/templates/PassengerStopAssignment.xml` Z. 16 | belegt |
| H6 | `Quay` und `ScheduledStopPoint` können dieselbe ID haben; Auflösung deshalb über (ID, erwarteter Typ). | Beispiel `src/examples/01_NeTEx_Spiez_Interlaken_Ost.xml` (`ch:1:sloid:7483:0:90840` als `Quay` und `ScheduledStopPoint`) | belegt |
| H7 | In `NETWORK_OFFER`-Dateien fehlen Haltestellen (Lieferanten senden `NETWORK_OFFER` und `INTERCHANGE`; `SITE_OFFER` nur für Daten, die nicht in ATLAS stehen); Verweise darauf sind `external_or_unloaded`, kein Fehler. | `src/02_files.md` Z. 142 (im Guide seit `d0a8e6d` `SITE_OFFER`, vorher `STOP_OFFER`); Beispiel 18 ohne `SiteFrame` | belegt |

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
| Z4 | **Welcher `TimingLink`:** Der `TimingLink` einer Fahrzeit wird über `StopPointInJourneyPattern/OnwardTimingLinkRef` bestimmt, wenn vorhanden. Sonst gilt der `TimingLink`, dessen `FromPointRef`/`ToPointRef` zu den beiden Halten passen (`src/templates/TimingLink.xml` Z. 56–65), mit ℹ Hinweis „über Von/Nach-Punkt bestimmt“. Beispiel 01 hat kein `OnwardTimingLinkRef`; es kommt nur in den Beispielen 06, 09, 13 und 18 vor. | `src/08_timetable.md` Z. 96; Entscheid (3) „Entscheide nach Review Phase 2“ | **festgelegt** (Benutzer, 31.10.2026), umgesetzt in Phase 3 (`timing.py`); der Hinweis steht je Strecke in der Rechenkette und einmal je Fahrt als Diagnose |
| Z5 | Abfahrt an einem Halt = Ankunft + `JourneyWaitTime/WaitTime` dieses `ScheduledStopPoint`. Bei mehrfachem Besuch desselben Halts gilt `StopPointInJourneyPatternRef` vor `ScheduledStopPointRef`. `TimingPointRef` ist im `JourneyWaitTime` ebenfalls erlaubt (wie `ScheduledStopPointRef`). | `src/08_timetable.md` Z. 97; `src/templates/TimeDemandType.xml` Z. 76–84 | belegt |
| Z5a | Ohne `JourneyWaitTime` für einen Halt gilt die Wartezeit 0, in der Rechenkette als **Standardwert** gekennzeichnet (kein Element als Quelle). Wartezeiten sind nur anzugeben, wenn sie grösser als 0 sind. | `src/templates/TimeDemandType.xml` Z. 75 („We only need wait times if greater than 0.“) | belegt |
| Z5b | Ist für einen Halt eine passende `JourneyWaitTime` vorhanden, aber ohne (oder mit leerer) `WaitTime`, ist die Abfahrt „nicht berechenbar“ mit Grund (Schlüssel `projection.time.wait_time_missing`); der Standardwert 0 (Z5a) gilt nur, wenn **keine** passende `JourneyWaitTime` existiert. Mehrere passende `TimingLink` ohne eindeutige `RunTime` im `TimeDemandType` sind „mehrdeutig“, nicht „nicht gefunden“ (Z4). | Folgt aus Z5a (Wortlaut „We only need wait times if greater than 0“ betrifft nur fehlende Einträge) und Z7 | belegt (Auslegung, Review Opus 31.10.2026) |
| Z6 | Zeiten sind Ortszeit `hh:mm:ss` ohne Zeitzone (Ausnahme: Z9). | `src/03_xml_modelling.md` Z. 232–237; `src/08_timetable.md` Z. 87 | belegt |
| Z7 | Fehlt ein Summand (`DepartureTime`, `RunTime`, `TimingLink`) oder ist er nicht eindeutig lesbar (Format, Monate/Jahre in der Dauer, mehrere passende Einträge), ist die Zeit „nicht berechenbar“ mit Grund; alle folgenden Zeiten der Fahrt ebenfalls (die Kette bricht ab). Kein Ersatzwert. | Projektregel „Nichts erfinden“ ([UMSETZUNGSPLAN.md](../UMSETZUNGSPLAN.md) Abschnitt 3) | belegt |
| Z8 | **Nächte der Zeitumstellung:** Zeiten sind Ortszeit ohne Zone; deshalb kein Doppeln der Fahrten für Sommer-/Winterzeit. Berührt eine Fahrt an einem Betriebstag die Stunde 02:00 bis 03:00 des Umstellungstags, entsteht ein ℹ Hinweis (nichts wird korrigiert); UTC-Zeiten (Z9) zählen dafür nicht. Umstellungstage: letzter Sonntag im März und im Oktober (Projektannahme, nicht im Guide). | `src/templates/ServiceJourney.xml` Z. 93; `src/08_timetable.md` Z. 87; Entscheid „Fahrten über Mitternacht“ | Auslegung |
| Z9 | **UTC-Zeit (Sonderfall Zeitumstellung, Entscheid A, 04.11.2026):** Eine zweite Fahrt in der wiederholten Stunde 02:00–03:00 bekommt eine eigene `sjyid` und eine `DepartureTime` in UTC, z. B. `02:33:00Z`. Das Tool liest `hh:mm:ssZ` als UTC (Kennzeichen, kein Ersatzwert), rechnet **nicht** in Ortszeit um und berechnet die Folgezeiten aus `RunTime`/`WaitTime` ebenfalls als UTC; Anzeige mit Zusatz „UTC“ (z. B. „01:33 UTC“), Rechenkette ebenso. Hinweis (ℹ) `projection.time.utc`. Vergleiche zwischen UTC- und Ortszeit (Zeiten einer `JourneyPart`) entfallen mit Hinweis `projection.part_time_utc`; UTC-Zeiten zählen nicht für den Hinweis Z8. Andere Zeitzonen (`+01:00` usw.) bleiben „nicht berechenbar“. | `src/08_timetable.md` Z. 99–102 („Very special case: two ServiceJourneys during change from summer to winter time“, Z. 102 „must be indicated as UTC. E.g. `02:33:00Z`“) | belegt (Umgang mit UTC: Entscheid A) |

## Mitternacht

| # | Regel | Beleg | Status |
|---|---|---|---|
| M1 | Fahrt beginnt nach Mitternacht, gehört aber zum Vortag: `DepartureDayOffset` = 1. | `src/uc10_midnight_passing.md` Z. 3–9 | belegt |
| M2 | `DepartureDayOffset` ist optional; fehlt es, gilt 0 (als Standardwert gekennzeichnet). Negativ nur sehr selten. | `src/templates/ServiceJourney.xml` Z. 94–98; `src/08_timetable.md` Z. 90 | belegt |
| M3 | Tageswechsel während der Fahrt hat kein eigenes Element; er folgt aus dem Aufsummieren von `DepartureTime` und `RunTime`/`WaitTime`. | `src/uc10_midnight_passing.md` Z. 11 ff.; `src/03_xml_modelling.md` Z. 236–237 | belegt |
| M4 | `JourneyPart` trägt den Tag ausdrücklich: `StartTime`/`StartTimeDayOffset`, `EndTime`/`EndTimeDayOffset`. Fehlt die Verschiebung, gilt 0 (als Standardwert gekennzeichnet). | `src/templates/JourneyPart.xml` Z. 82–85 | belegt |
| M5 | Jede Zeit trägt die Verschiebung zum Betriebstag („+1“, „−1“). Sie ist **ausdrücklich** (`DepartureDayOffset` steht in der Datei), **Standardwert** (fehlt, 0) oder **berechnet** (Aufsummieren hat den Tag gewechselt). | `src/03_xml_modelling.md` Z. 232–237; `src/uc10_midnight_passing.md` Z. 3–18 | belegt |

## Betriebstage

| # | Regel | Beleg | Status |
|---|---|---|---|
| B1 | Betriebstage über `AvailabilityConditionRef` → `AvailabilityCondition` (`FromDate`, `ToDate`, `ValidDayBits`), nicht über `DayType`. | `src/08_timetable.md` Z. 81 („Day Governance“) | belegt |
| B2 | `ValidDayBits`: genau ein Bit je Kalendertag des Zeitraums, `1` = gültig. | `src/07_service_calendars.md` Z. 111 | belegt |
| B3 | Nur ein `AvailabilityConditionRef` je `ServiceJourney`. | `src/templates/ServiceJourney.xml` Z. 16–19 | belegt |
| B4 | `DayType`/`DayTypeAssignment` nur für nationale Feiertage. | `src/07_service_calendars.md` Z. 165, 217, 232 | belegt |
| B5 | Ein einzelner Tag wird als `…T00:00:00` bis `…T23:59:59` beschrieben. | `src/03_xml_modelling.md` Z. 224–229 | belegt |
| B6 | Tag *i* (ab 0) der Bitfolge ist `FromDate` + *i* Tage. Weicht die Länge von der Zahl der Tage zwischen `FromDate` und `ToDate` (beide eingeschlossen) ab, werden die Tage **nicht** aufgelistet (die Zuordnung wäre geraten); die Anzahl gesetzter Bits und eine △ Warnung bleiben. In 15 der 22 Beispiele weicht die Länge ab ([assumptions.md](assumptions.md)). | `src/07_service_calendars.md` Z. 111 („exactly one bit per calendar day of the period“) | belegt |
| B7 | Die `AvailabilityCondition` steht zentral im `ServiceCalendarFrame`, nie eingebettet in der Fahrt. Die Fahrtansicht folgt deshalb nur `AvailabilityConditionRef`. | `src/07_service_calendars.md` Z. 111 („never inline“) | belegt |

## Fahrtbezeichnung

| # | Regel | Beleg | Status |
|---|---|---|---|
| F1 | Zugnummer über `trainNumbers/TrainNumberRef` → `TrainNumber` (`ForAdvertisement`). | `src/templates/ServiceJourney.xml` Z. 119–121; Beispiel 01 | belegt |
| F2 | Schweizer Fahrt-ID (sjyid) in `privateCodes/PrivateCode` mit `type="sjyid"`, nicht in `keyList`. | `src/08_timetable.md` Z. 89; `src/templates/ServiceJourney.xml` Z. 23, 37–41 | belegt |

## Referenzen (Phase 2)

Umgesetzt in `app/core/index/references.py`; Entscheide in [decisions.md](decisions.md) („Zieltyp von Referenzen“, „Nicht gefundenes Ziel einer Referenz“). Geprüft an `5faccdec` und den 22 gegenüber `d0a8e6d` unveränderten Beispielen: 1492 Referenzen, davon 1487 aufgelöst, 4 `external_or_unloaded` (Beispiel 17, `FromPointRef`/`ToPointRef`) und 1 nicht aufgelöst (`ParentSiteRef` auf `ch:1:sloid:169` in Beispiel 23). Die zuvor hier `d0a8e6d` zugeschriebenen 1520/1516 Referenzen ohne nicht auflösbares Ziel waren veraltet; am 06.11.2026 nach Rückfrage berichtigt.

| # | Regel | Beleg | Status |
|---|---|---|---|
| R1 | Eine Referenz ist ein Element mit Attribut `ref`, das auf `Ref` endet oder `nameOfRefClass` trägt; sie steht an beliebiger Stelle, auch in `Extensions`. | `xsd/xsd/*.xsd` (Ref-Elemente tragen `ref`, `version`/`versionRef`, `nameOfRefClass`); `src/02_files.md` | belegt |
| R2 | Erwarteter Zieltyp: `nameOfRefClass`, sonst `config/ref-targets.json`, sonst Name ohne `Ref`. | XSD-Deklaration je Ref-Element (`<xsd:element name="…Ref" type="…RefStructure">`); Test `tests/guide/test_ref_targets.py` prüft jeden Eintrag gegen die XSD | belegt |
| R3 | Die Liste enthält je Ref-Namen **alle** laut XSD erlaubten Zieltypen: die Aufzählung `NameOfClass…RefStructureType` am Attribut `nameOfRefClass` des Ref-Typs (`xsd/xsd/netex_framework/netex_responsibility/netex_entity_support.xsd`), bei Ref-Elementen ohne eigenen `type` die des Kopfelements der `substitutionGroup`; deklariert die XSD denselben Namen mit mehreren Ref-Typen (`FromPointRef`/`ToPointRef`: 9 Typen), gilt die Vereinigung. Aufgenommen sind die 47 Ref-Namen der Beispiele und Vorlagen mit abweichendem Zieltyp (z. B. `OnwardTimingLinkRef` → `ServiceLink`, `TimingLink`; `ResponsibleOrganisationRef` → 9 Organisationsklassen). Ausnahmen (Entscheid „Entscheide nach Review Phase 2“, [open-points.md](open-points.md) 8–10): `…PointInPatternRef` (XSD: jede Klasse) behält `StopPointInJourneyPattern`; `ParentJourneyRef` enthält zusätzlich `ServiceJourney` (Beispiel 21); `FromProductCategoryRef`/`ToProductCategoryRef` sind in der XSD nicht deklariert. | `xsd/xsd/…`, Beispiele und Vorlagen | belegt |
| R4 | Mehrere Objekte mit gleicher ID und gleichem Typ: `version`/`versionRef` der Referenz entscheidet (ausser `any`); sonst mehrdeutig. Eine abweichende Version bei genau einem Objekt ändert den Status nicht, ergibt aber den ℹ Hinweis `reference.version_differs`. | Projektentscheid (Phase 2); `version="any"` kommt in der 1.10-Lieferung vor ([open-points.md](open-points.md), Archiv Punkt 6) | belegt |

## Verkehrsmittel und Produktkategorie (Phase 3)

| # | Regel | Beleg | Status |
|---|---|---|---|
| V1 | `TransportMode` ist an der `Line` Pflicht, an der `ServiceJourney` optional; `TransportSubmode` (Kindelement `…Submode`, z. B. `RailSubmode`) ist an der `Line` optional. In zwei Fahrten der Beispiele (07) steht `TransportSubmode` auch in der `ServiceJourney`; die Vorlage nennt es nicht, es wird gezeigt, wenn vorhanden. Die Fahrtansicht zeigt beides getrennt nach Quelle (Fahrt, Linie). | `src/templates/Line.xml` Z. 42–47; `src/templates/ServiceJourney.xml` Z. 55–58 | belegt |
| V2 | Codes von `TransportMode` und `TransportSubmode` stehen nicht in den Stammdaten der Mappingtabelle als Erläuterung (Blatt `VMArt->NeTEx` ordnet Produkte Modus und Submodus zu, erklärt sie aber nicht): Anzeige des Codes mit „keine Erläuterung in den Stammdaten“. Die Tabelle in `uc06_modes_submodes.md` ist nicht die Mappingtabelle und wird nicht verwendet. | `src/uc06_modes_submodes.md` Z. 33; Entscheid „Anzeige von Codes und Stammdaten“ | belegt |
| V3 | `TypeOfProductCategoryRef` ist an `ServiceJourney` und `Line` Pflicht („Relevant elements are defined in the mapping excel“). `TypeOfProductCategory` hat `Name` (mehrsprachig, Pflicht) und `ShortName` (Pflicht). Das Produkt kann in einer `JourneyPart` wechseln (`TypeOfProductCategoryRef` dort). Die Fahrtansicht zeigt Fahrt, Linie (und Teilstrecke) getrennt. | `src/templates/ServiceJourney.xml` Z. 59–62; `src/templates/Line.xml` Z. 60–63; `src/templates/TypeOfProductCategory.xml` Z. 23–28; `src/templates/JourneyPart.xml` Z. 97–100 | belegt |
| V4 | Bedeutung der Produktkategorie: Name aus der Datei; zusätzlich die Zeile des Blatts `VMArt->NeTEx`, deren `Abk` gleich dem `ShortName` ist (Blatt, Zeile, Guide-Stand). Ohne Treffer: „keine Erläuterung in den Stammdaten“. | `src/03_xml_modelling.md` Z. 206–207 (die ID wird aus dem `ShortName` gebildet); `src/02_files.md` Z. 29 (Produktkategorien stehen in der Mappingtabelle); `src/uc06_modes_submodes.md` Z. 35–37 | Auslegung (Spalte `Abk` ↔ `ShortName`) |

## Angebote (Phase 3)

| # | Regel | Beleg | Status |
|---|---|---|---|
| A1 | Ein `ServiceFacilitySet` beschreibt die Angebote einer `ServiceJourney` oder einer `JourneyPart`. Seine Gruppen (z. B. `CateringFacilityList`, `FareClasses`, `PassengerCommsFacilityList`) sind Listen: mehrere Codes, getrennt durch Leerraum. Jeder Code wird einzeln und unverändert gezeigt. | `src/09_resources.md` Z. 206, 219–235 | belegt |
| A2 | Die Fahrt verweist mit `facilities/ServiceFacilitySetRef` auf ihre Angebote (ganze Fahrt). Die Vorlage `ServiceJourney.xml` nennt `facilities` nicht; es kommt in 4 Fahrten der Beispiele (02, 03, 08) vor. | Beispiel 08 Z. 447–449; `src/09_resources.md` Z. 206 | Auslegung |
| A3 | Die `JourneyPart` verweist mit `facilities/ServiceFacilitySetRef` auf die Angebote nur dieser Teilstrecke (Wechsel der Angebote, z. B. Bistro nur zwischen Bern und Olten); mit `validityConditions` kann sie auf einzelne Tage beschränkt sein. | `src/templates/JourneyPart.xml` Z. 55–61, 90–96; `src/uc05_journey_parts.md` Z. 29–66 | belegt |
| A4 | Bedeutung eines Angebots-Codes: Blatt `Angebote`, Spalte `Facility Value` gleich dem Code (exakt; mehrere Zeilen werden alle gezeigt). Gezeigt werden Angebotabkürzung, Angebottext und die übrigen Spalten mit Blatt, Zeile und Guide-Stand. Ohne Treffer: „keine Erläuterung in den Stammdaten“. | `src/09_resources.md` Z. 237; `src/uc04_service_facilities.md` Z. 10, 20; Entscheid „Mappingtabelle auslesen“ | belegt |
| A5 | `FromStopPointRef`/`ToStopPointRef` einer `JourneyPart` nennen den `ScheduledStopPoint` (auf Quay-Ebene), an dem die Teilstrecke beginnt/endet; fehlt das Ende, reicht sie bis zum Ende der Fahrt. Die Halte der Teilstrecke sind alle Halte vom Anfang bis zum Ende (XML-Reihenfolge). Kommt der Fahrplanpunkt in der Haltefolge mehrfach vor oder steht er nicht darin, wird die Teilstrecke nicht den Halten zugeordnet; das steht bei der Teilstrecke. Für `FromPointInPatternRef`/`ToPointInPatternRef` (Kurswagen) siehe P3. | `src/templates/JourneyPart.xml` Z. 74–81; Beispiel 21 Z. 454–491 | belegt (Verweise auf Halte anderer Fahrtmuster: Auslegung) |
| A6 | `StartTime` einer Teilstrecke ist die Abfahrt am Anfangshalt, `EndTime` die Ankunft am Endhalt. Weichen sie von den berechneten Zeiten ab, entsteht eine △ Warnung (nicht prüfbar, wenn die Halte nicht zugeordnet sind). Geprüft an Beispiel 08: alle vier Zeiten stimmen. | `src/templates/JourneyPart.xml` Z. 82–85 („Time bounds of the part“); Beispiel 08 | Auslegung |
| A7 | Die Angebote einer Teilstrecke und die der ganzen Fahrt werden **nicht** zu einer „gültigen Menge“ verrechnet. `uc05` sagt seit `d0a8e6d`, die Menge der Teilstrecke sei „valid for this part only“ (vorher „overrides“ die der Fahrt); Beispiel 08 meint ergänzend („the two attributes that are valid for the whole ServiceJourney“). Die Fahrtansicht zeigt beide getrennt ([assumptions.md](assumptions.md), [open-points.md](open-points.md)). | `src/uc05_journey_parts.md` Z. 155 („valid for this part only“; bis `b7ac158` Z. 104 „overrides“); Beispiel 08 Z. 456–458 | offen |

## Hinweise (Phase 3)

| # | Regel | Beleg | Status |
|---|---|---|---|
| N1 | `NoticeAssignment` verbindet einen `Notice` mit einem Element. Die Fahrtansicht zeigt eine Zuweisung, wenn sie in der `ServiceJourney` eingebettet ist (`noticeAssignments`), im `ServiceJourneyPattern` der Fahrt, in einem `StopPointInJourneyPattern` dieses Musters, oder wenn sie auf Frame-Ebene die Fahrt (`ServiceJourneyRef`, `NoticedObjectRef`) oder das Fahrtmuster (`JourneyPatternRef`) nennt. | `src/templates/NoticeAssignment.xml` Z. 22, 35; `src/templates/ServiceJourney.xml` Z. 67–78; `src/06_service.md` Z. 89, 105 | belegt (Frame-Ebene mit Verweis: Auslegung, Beispiele 02, 05, 08, 10) |
| N2 | Gilt der Hinweis nur für einen Teil der Fahrt, nennen `StartPointInPatternRef`/`EndPointInPatternRef` die Halte. Die Fahrtansicht zeigt „ab Halt n bis Halt m“, wenn die Verweise auf Halte des Fahrtmusters dieser Fahrt zeigen. | `src/templates/NoticeAssignment.xml` Z. 37–43; `src/uc05_journey_parts.md` Z. 137 | belegt |
| N2a | Fehlt `EndPointInPatternRef`, endet die Gültigkeit am Startpunkt („gleich wie Start Point“); die Fahrtansicht setzt den Endhalt gleich dem Starthalt. | `xsd/xsd/netex_framework/netex_reusableComponents/netex_noticeAssignment_version.xsd` Z. 190–194 (`EndPointInPatternRef`: „If absent same as Start Point.“), XSD-Stand `73b337e` | belegt |
| N3 | Eine `NoticeAssignment` auf Frame-Ebene ohne `NoticedObjectRef`, `ServiceJourneyRef` und `JourneyPatternRef` (Beispiel 08, `na-1`/`na-2`) gehört zu keiner bestimmten Fahrt. Sie wird nicht angezeigt; die Anzahl steht als ℹ Hinweis. | Beispiel 08 Z. 509–514 | offen ([open-points.md](open-points.md)) |
| N4 | Texte des `Notice` erscheinen unverändert in allen Sprachen: `Text` mit `lang`, verschachtelte `Text`-Elemente und (obwohl die Vorlage sie verbietet) `alternativeTexts/AlternativeText/Text` mit ihrem `attributeName`. Zusätzlich `ShortCode` und der Name des `TypeOfNotice`. Erlaubt sind `TypeOfNotice` 1 und 10 (11 entfällt). | `src/templates/Notice.xml` Z. 26–48; `src/09_resources.md` Z. 108–113 | belegt |

## Teilstrecken (Phase 3)

| # | Regel | Beleg | Status |
|---|---|---|---|
| P1 | Eine `JourneyPart` ist eine Teilstrecke einer Fahrt mit eigenen Eigenschaften (Angebote, Produkt, Zugnummer, Betreiber). Zweck: `PurposeOfJourneyPartitionRef` (erlaubt `FacilityChange`, `DirectCarriage`, `TypeOfProductCategoryChange`). | `src/uc05_journey_parts.md` Z. 9, 22–25, 29–66, 68–110; `src/templates/JourneyPart.xml` Z. 86–89 (Z. 88) | belegt |
| P2 | Kurswagen werden mit `JourneyPart` abgebildet (`PurposeOfJourneyPartition:DirectCarriage`, `ParentJourneyRef` nennt die ziehende Fahrt, `FromPointInPatternRef`/`ToPointInPatternRef` zeigen auf deren Fahrtmuster). **Aufgelöst:** Der frühere Widerspruch (`uc08` sagte bis `b7ac158`, `JourneyPart` werde nicht verwendet) besteht seit `d0a8e6d` nicht mehr ([assumptions.md](assumptions.md) Nr. 6). | `src/uc08_kurswagen.md` Z. 41–66; `src/uc05_journey_parts.md` Z. 68–110, 154; `mgmt/Decisions.md` Z. 42; Beispiel 21 Z. 449–492 | belegt |
| P3 | **Kurswagen-Teilstrecken den Halten zuordnen (Entscheid B, 04.11.2026):** `FromPointInPatternRef`/`ToPointInPatternRef` zeigen auf einen Punkt im Fahrtmuster der ziehenden Fahrt (`ParentJourneyRef`). Liegt der Punkt im eigenen Fahrtmuster, gilt seine Position. Sonst gilt sein `ScheduledStopPointRef`: Genau ein Halt im eigenen Fahrtmuster mit demselben `ScheduledStopPoint` ergibt die Position (Beispiel 21: Teilstrecken 1–2, 2–3, 3–4); bei keinem oder mehreren Treffern bleibt es bei „keine Zuordnung“ (nichts raten). | `src/uc05_journey_parts.md` Z. 154 („reference points in the `ServiceJourneyPattern` of the pulling train given in `ParentJourneyRef`“); `src/uc08_kurswagen.md` Z. 54–58 | Auslegung (Zuordnung über den Fahrplanpunkt: Entscheid B) |

## Eigene Dateien und Validierung (Phase 4)

Umgesetzt in `app/core/intake.py`, `app/core/validation/` (`detection.py`, `lxml_checks.py`, `core_rules.py`, `engine.py`) und `app/core/guide/links.py`. Die Kernregeln selbst (30 Stück) stehen mit Vorlage, Zeilen und Entscheiden in [core-rules.md](core-rules.md).

| # | Regel | Beleg | Status |
|---|---|---|---|
| D1 | **Versionserkennung** sammelt Hinweise und gewichtet sie (stark = 2 Punkte, schwach = 1): `version` der Wurzel `2.x` bzw. `1.10` (stark), `schemaLocation` mit `/schema/1.10/` bzw. `/schema/2.x/` (stark) oder mit `xsd/xsd/NeTEx_publication.xsd` (schwach, Guide-Beispiele zeigen relativ auf die XSD des Guides), Kommentar `Profile: …` (schwach, 1.10), Dateiname mit `NETWORK_OFFER`/`SITE_OFFER`/`INTERCHANGE` (schwach, 2.0), Struktur `ServiceJourneyPattern` und `TimeDemandType` (stark, 2.0), `calls` in einer `ServiceJourney` (schwach, 1.10). `erkannt` verlangt zwei verschiedene Hinweise und zwei Punkte Vorsprung; sonst `mehrdeutig` (Hinweise ohne klaren Sieger) oder `unbekannt`. Das Wurzelattribut entscheidet nie allein. Die 22 Beispiele (auch 01 und 20 mit `version="1.09"`, 08 ohne Attribut) ergeben CH 2.0, `fixtures/netex110_like.xml` ergibt 1.10. | `src/examples/*.xml` (Köpfe), [research/delivery-1.10-2027.md](research/delivery-1.10-2027.md) („Kopf jeder Datei“, „Nicht vorhanden“, „Versionsangaben“); `src/02_files.md` Z. 163 (Dateityp im Namen) | Auslegung (Gewichte von Claude, technische Festlegung) |
| D2 | `calls` zählt nur schwach für 1.10: Das Profil 2.0 verbietet `calls` (CH-SJ-13), sie kommen aber in fehlerhaften 2.0-Dateien vor (`fixtures/ch20_calls.xml`), die dann trotzdem als 2.0 geprüft werden müssen, damit die Kernregel anschlägt. | `src/templates/ServiceJourney.xml` Z. 145–153 | Auslegung |
| D3 | Nur als **CH 2.0 erkannte** Dateien werden geprüft; andere Dateien zeigen die Erkennung mit Begründung und bleiben im Explorer nutzbar. | Entscheid „Eigene Dateien prüfen“ ([decisions.md](decisions.md)) | festgelegt |
| D4 | **XSD:** `xsd/xsd/NeTEx_publication.xsd` des Guide-Klons, mit lxml geladen (rund 17 s, einmal), Meldung im Originalwortlaut ohne Namensraum-Präfix. libxml2 nennt meist Spalte 0; die Stelle ist der Beginn der Zeile (hinter der Einrückung). | Entscheid „Prüfergebnisse Guide-Beispiele“; erneut bestätigt in `5faccdec`: alle 22 Beispiele XSD-gültig | belegt |
| D5 | **`general_rules.sch`:** vier Muster (`no_version_any`, `no_versionRef_any`, `ref_elements_require_version`, `no_order_attribute`) mit `lxml.isoschematron`; jeder Verstoss mit Zeile des Elements. Stand `5faccdec`: keine Verstösse in den 22 Beispielen, wie bereits bei `d0a8e6d`. Historisch (`b7ac158`): 121 `order`-Verstösse in **9** Beispielen (02: 1, 03: 11, 08: 14, 12: 3, 14: 2, 19: 5, 20: 8, 21: 11, 22: 66). | `src/schematron_rules/general_rules.sch`; [test-report.md](test-report.md) „Guide-Update 5faccdec“ | belegt |
| D6 | **Link zum Guide-Kapitel:** über `src/A5_annex_index.md` das erste Kapitel (`NN_…`, `ucNN_…`) des Elementnamens, auf GitHub im geprüften Commit. Tabellenseiten (`site/tables/…`), Anhänge und `index` zählen nicht. | Entscheid „Validierung mit Erklärung“ (4) | Auslegung (erstes Kapitel der Liste) |
| D7 | **Rumpf-Fahrt:** `ServiceJourney` ohne `ServiceJourneyPatternRef`, die nur `privateCodes` enthält (Erkennung am Inhalt, nicht am Dateinamen); die Fahrt-Kernregeln gelten nicht, es entsteht ein ℹ Hinweis. In den Guide-Beispielen nur 3 Fahrten in Beispiel 17. | `examples/17_NeTEx_CH_INTERCHANGE.xml` Z. 27–41; Entscheid „Kernregeln Phase 4“ (1) | festgelegt |


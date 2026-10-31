# Annahmen und Widersprüche im Guide

Stand: Phase 3 (31.10.2026), Guide `b7ac158`, XSD `73b337e`. Hier stehen (1) Widersprüche und Auffälligkeiten im Guide und in seinen Beispielen und (2) Annahmen, die das Tool trifft, weil der Guide-Text etwas nicht ausdrücklich sagt. Das Tool meldet nichts an den Guide (Entscheid „Fehler in Guide-Dateien“); es zeigt, was in der Datei steht, und macht Unsicherheiten in der Anwendung sichtbar. Belege zu den Regeln: [mapping.md](mapping.md). Offene Fragen an den Benutzer: [open-points.md](open-points.md).

## Widersprüche und Auffälligkeiten im Guide

### 1. Beispiel 01: Kommentar 10:53, Daten ergeben 10:54

Der Kommentar am Anfang von `01_NeTEx_Spiez_Interlaken_Ost.xml` nennt die Ankunft in Interlaken Ost um 10:53. Die Daten ergeben 10:54: `DepartureTime` 10:35 + `RunTime` `tl-1` PT10M + `WaitTime` PT3M in Interlaken West + `RunTime` `tl-2` PT6M. Es gibt keine weiteren Summanden (kein `OnwardTimingLinkRef`, die Strecken ergeben sich über `FromPointRef`/`ToPointRef`). Das Tool zeigt 10:54 mit Rechenkette, jeder Summand mit Quelle. Ein Test (`tests/guide/test_example_journeys.py`) hält den Kommentar fest und meldet „Beispiel geändert – Erwartung prüfen“, sobald sich das Beispiel ändert. **Geklärt (Plan Phase 3):** Fehler im Kommentar oder in den Zeiten des Beispiels, nicht im Tool.

### 2. `examples/README.md` erwähnt noch `PassingTimes`

`src/examples/README.md` beschreibt Beispiel 02 mit `PassingTimes` und Beispiel 07 mit `TimetabledPassingTimes`. Alle 22 Beispiel-Dateien verwenden stattdessen `ServiceJourneyPattern` + `TimeDemandType` (kein `TimetabledPassingTime`, kein `Call`). Massgebend sind die Dateien; die Vorlagen `TimetabledPassingTime_deprecated.xml` und `ServiceJourney_PassingTime_deprecated.xml` sind als veraltet markiert.

### 3. `ValidDayBits` passt in 15 von 22 Beispielen nicht zum Zeitraum

Der Guide verlangt „genau ein Bit je Kalendertag des Zeitraums“ (`07_service_calendars.md` Z. 111). Geprüft am Stand `b7ac158` (Tage zwischen `FromDate` und `ToDate`, beide eingeschlossen, gegen die Länge der Bitfolge):

| Beispiel | Zeitraum | Tage | Bits | Bemerkung |
|---|---|---|---|---|
| 01, 02, 06, 07, 08, 09, 10, 11, 13, 17, 18, 20 | 14.12.2025 – 13.12.2026 | 365 | 373 | 8 Bits zu viel; ein Bit gesetzt (Index 320) |
| 04 | 14.12.2025 – 10.12.2026 | 362 | 251 | zu kurz |
| 05 | 14.12.2025 – 10.12.2026 | 362 | 239 | zu kurz |
| 14 | 15.12.2025 – 12.12.2026 | 363 | 7 | 5 Bits gesetzt: sieht nach einem Wochenmuster aus |
| 03, 12, 15, 21, 22 | | | | stimmen |

Das Tool listet die Tage nur, wenn die Länge stimmt (Regel B6), und zeigt sonst die Anzahl gesetzter Bits mit einer △ Warnung. Es rät nicht, wie die Bits den Tagen zuzuordnen wären. Beispiel 16 und 19 haben keine `ValidDayBits`.

### 4. Beispiel 01: `StopPlace` „Bern“ für Spiez, fünfstellige Jahreszahl

`StopPlace` `ch:1:sloid:7483` trägt `Name` „Bern“ und `AlternativeText` „Spiez“; `ValidBetween/FromDate` lautet `20205-12-14T00:00:00` (fünfstellige Jahreszahl; die XSD lässt das zu). Das Tool zeigt den `Name` aus der Datei („Bern“) neben dem Namen des Fahrplanpunkts „Spiez“. Nichts wird korrigiert.

### 5. `uc05`: Angebote der Teilstrecke „überschreiben“ die der Fahrt, Beispiel 08 meint ergänzend

`uc05_journey_parts.md` Z. 104: „`ServiceFacilitySet` defined on a `JourneyPart` overrides the one on the `ServiceJourney` for that section.“ In Beispiel 08 stehen an der Fahrt `firstClass` und `freeWifi` (Kommentar: „the two attributes that are valid for the whole ServiceJourney“) und an den Teilstrecken `bistro` („the restaurant when it is open“); gemeint ist offensichtlich ergänzend, nicht ersetzend. Das Tool zeigt die Angebote der ganzen Fahrt und die der Teilstrecken getrennt und rechnet keine „gültige Menge“ aus (offener Punkt).

### 6. Kurswagen: `uc08` sagt „kein `JourneyPart`“, Beispiel 21 verwendet `JourneyPart`

`uc08_kurswagen.md` Z. 43: „`JourneyPart` and `JourneyPartCouple` are **not used** for this in RG 2.0.“ Beispiel 21 bildet den Kurswagen Zürich–Bremen mit drei `JourneyPart` ab (`ParentJourneyRef`, `FromPointInPatternRef`/`ToPointInPatternRef`, `PurposeOfJourneyPartition` `DirectCarriage`); `uc05` §3 bis §5 nennen weitere Verwendungen als „not used“. Das Tool zeigt die Teilstrecken aus der Datei. Die Verweise zeigen auf Halte der Fahrtmuster der Zubringerzüge, nicht auf Halte der Kurswagen-Fahrt; deshalb werden die Teilstrecken nicht den Halten der Fahrt zugeordnet.

### 7. Hinweiszuweisungen auf Frame-Ebene ohne Ziel (Beispiel 08)

In Beispiel 08 stehen im `TimetableFrame` zwei `NoticeAssignment` (`na-1`, `na-2`) nur mit `NoticeRef`, ohne `NoticedObjectRef`, `ServiceJourneyRef` oder `JourneyPatternRef`. Die Vorlage `NoticeAssignment.xml` verlangt die Einbettung in das betroffene Element. Das Tool zeigt solche Zuweisungen keiner Fahrt zu und meldet ihre Anzahl als ℹ Hinweis (offener Punkt).

### 8. `alternativeTexts` im `Notice`

Die Vorlage `Notice.xml` verbietet `alternativeTexts` (Mehrsprachigkeit über verschachteltes `Text`). Beispiel 08 verwendet sie, teils ohne `lang`. Das Tool zeigt alle Texte unverändert und kennzeichnet die aus `AlternativeText` mit ihrem `attributeName`.

### 9. Beispiel 04: `RunTime` „P3M“

Beispiel 04 enthält `<RunTime>P3M</RunTime>` (drei Monate, vermutlich PT3M gemeint). Monate sind keine feste Dauer; die Zeiten dieser Fahrt sind „nicht berechenbar“ mit Grund. In derselben Datei hat bei zwei Fahrten je eine Strecke keinen `TimingLink`; in Beispiel 07 (Fahrt `…4208-003B_DB`, Basel Bad – Freiburg) ebenso, in Beispiel 11 fehlt für `ch:1:TimingLink:8215-8218` die `RunTime`. Das Tool lässt diese Lücken sichtbar.

### 10. Beispiel 19: `AvailabilityCondition` ohne `ValidDayBits`

`NJ470_IC60470` hat `FromDate` 2026-01-01T00:00:00 und `ToDate` 2026-12-31T00:00:00, aber keine `ValidDayBits`. Betriebstage sind nicht bestimmbar; die Fahrtansicht meldet das als △ Warnung.

### 11. Wenige Beispiele nennen den `OnwardTimingLinkRef`

`08_timetable.md` Z. 97 sagt, der `TimingLink` stehe im `OnwardTimingLinkRef`. Nur die Beispiele 06, 09, 13 und 18 verwenden ihn; alle anderen ergeben die Strecken nur über `FromPointRef`/`ToPointRef`. Festlegung des Benutzers (Regel Z4): `OnwardTimingLinkRef`, sonst Von-/Nach-Punkt mit ℹ Hinweis.

## Annahmen des Tools

| # | Annahme | Begründung | Wirkung |
|---|---|---|---|
| a | `Abk` in `VMArt->NeTEx` entspricht dem `ShortName` der `TypeOfProductCategory`. | Die ID wird aus dem `ShortName` gebildet (`03_xml_modelling.md` Z. 202–203); die Tabelle enthält die Produktkategorien (`02_files.md` Z. 29). | Die Zeile der Tabelle erscheint als Bedeutung. Ohne Treffer: „keine Erläuterung in den Stammdaten“. |
| b | Codes werden mit der Spalte `Facility Value` des Blatts `Angebote` verglichen; mehrere Treffer werden alle gezeigt (z. B. `cyclesAllowed` in sechs Zeilen). | Die Tabelle nennt das Facility und seinen Wert; der Guide verweist für die Bedeutung auf die Tabelle. | Der Code bestimmt nicht immer eine Zeile eindeutig; das Tool wählt keine. |
| c | Beim Vergleich mit den Stammdaten bleibt umgebender Leerraum unberücksichtigt (die Tabelle enthält z. B. `regionalRail␣`); sonst exakt. | Tippfehler und Leerzeichen der Tabelle bleiben unverändert sichtbar (Entscheid „Mappingtabelle auslesen“). | Treffer auch bei überzähligem Leerzeichen. |
| d | `StartTime` einer `JourneyPart` ist die Abfahrt am Anfangshalt, `EndTime` die Ankunft am Endhalt. | Der Guide sagt nur „Time bounds of the part“. Beispiel 08: alle vier Zeiten stimmen mit den berechneten überein. | Abweichungen sind △ Warnungen. |
| e | Die Zeitumstellung findet am letzten Sonntag im März (02:00 → 03:00) und im Oktober (03:00 → 02:00) statt. | Regel der Schweiz/EU; der Guide nennt sie nicht. | ℹ Hinweis, wenn eine Fahrt die Stunde 02:00 bis 03:00 eines Umstellungstags berührt. Die Tage kommen aus `ValidDayBits`; ohne verlässliche Tage kein Hinweis. |
| f | Frame-Ebene: Eine `NoticeAssignment` mit `JourneyPatternRef` gilt für alle Fahrten dieses Fahrtmusters (Beispiel 08), mit `ServiceJourneyRef` für diese Fahrt (Beispiele 02, 05, 10). | Die Vorlage sieht nur die Einbettung vor; die Beispiele verwenden die Verweise. | Die Hinweise erscheinen mit ihrem Geltungsbereich (Fahrt, Fahrtmuster, Halt, Strecke). |
| g | Keine `JourneyWaitTime` heisst Wartezeit 0. | `TimeDemandType.xml` Z. 75: Wartezeiten nur, wenn grösser als 0. | Standardwert in der Rechenkette gekennzeichnet. |
| h | Fehlendes `DepartureDayOffset` heisst 0. | `ServiceJourney.xml` Z. 94–98 („0 for current operating day“). | Standardwert gekennzeichnet, ℹ Hinweis. |

## Prüfung der Kurswagen-Betriebstage (Beispiel 21)

Plan Phase 3: „Betriebstage ggf. über `ValidDayBits` prüfen“. Der Kurswagen `KW37` startet an jedem Betriebstag; seine dritte Teilstrecke beginnt um 06:44 mit `StartTimeDayOffset` 1, die anschliessende Fahrt 2746 startet 06:44 mit `DepartureDayOffset` 0. Beides ist konsistent, wenn 2746 am Folgetag verkehrt. Alle vier Fahrten der Datei haben dieselbe `AvailabilityCondition` `KW37` (2026-01-01 bis 2026-12-31, alle 365 Bits gesetzt); die Verschiebung um einen Tag ist damit an den Rändern des Jahres nicht prüfbar (der Kurswagen am 31.12.2026 hätte seine Anschlussfahrt am 01.01.2027, ausserhalb des Zeitraums). Eine automatische Prüfung der Betriebstage zwischen Teilstrecke und Elternfahrt ist nicht umgesetzt ([open-points.md](open-points.md)).

# Schweizer Kernregeln für den Fahrplan

Schritt a von Phase 4 ([UMSETZUNGSPLAN.md](../UMSETZUNGSPLAN.md) Abschnitt 8; Entscheid „Profilregeln“ in [decisions.md](decisions.md)). Die Regeln sind selbst hergeleitet aus den Vorlagen des Guides `netexRealisationGuideSwitzerland`, Branch `next`, Commit **`b7ac158`** (`git rev-parse --short HEAD` ergibt `b7ac1586`; gleicher Stand wie in [mapping.md](mapping.md)). Pfade relativ zu `../netexRealisationGuideSwitzerland/src/`. Zeilenangaben gelten für diesen Commit.

**Stand:** Entwurf zur Freigabe durch den Benutzer. Es ist **kein Programmcode** umgesetzt. Die Regeln mit Status „unklar“ und die Fragen unten werden einzeln geklärt (siehe [open-points.md](open-points.md) Punkt 1), erst danach folgt die Umsetzung als Prüfschritte.

## Herleitung

- **Quellen:** `templates/ServiceJourney.xml`, `templates/ServiceJourneyPattern.xml`, `templates/TimeDemandType.xml`; wo eine Regel es verlangt `templates/TimingLink.xml` und `templates/JourneyPart.xml`; dazu Kapiteltexte (`08_timetable.md`, `02_files.md`, `uc05_journey_parts.md`).
- **Lesart der Kommentare** (`03_xml_modelling.md` Z. 242, `01_intro_roadmap.md` Z. 22):
  - `ch-usage: mandatory` = Pflicht. Ein Kindelement mit `mandatory` ist nur Pflicht, **wenn sein Elternelement vorhanden ist** (z. B. `ForBoarding` je `StopPointInJourneyPattern`).
  - `ch-usage: forbidden` = verboten.
  - `ch-usage: expected` = „fast immer erwartet“. Der Guide sagt ausdrücklich, dass manche Angaben bei fremden Fahrten nicht Pflicht sein konnten und deshalb nur „expected“ sind. Wird nur als **Hinweis** vorgeschlagen (Frage 3).
  - `ch-usage: optional` und `ignored` ergeben keine Regel.
  - `ch-allowed-enums` und `ch-note` mit „only“/„always“ ergeben Wertregeln.
- **Anwendungsbereich:** Die Regeln gelten je Objekt der genannten Art (`ServiceJourney`, `ServiceJourneyPattern`, `TimeDemandType`, `TimingLink`, `JourneyPart`), nicht für `TemplateServiceJourney` (eigene Vorlage, siehe „Bewusst nicht als Kernregel“). Für `ServiceJourney` in Dateien vom Typ `INTERCHANGE` ist der Anwendungsbereich offen (Frage 1).
- **Schweregrade** (Symbole nach [decisions.md](decisions.md) „Symbol für Warnung“): ⚠ Fehler, △ Warnung, ℹ Hinweis. Vorschlag: Pflicht fehlt, Verbotenes vorhanden und Wert ausserhalb der erlaubten Werte = ⚠ Fehler; `expected` und „sollte“ = ℹ Hinweis. Der Guide ist ein Entwurf; das Ergebnis heisst deshalb „geprüft gegen Entwurf `b7ac158`“, nie „gültig“. Ob „Fehler“ für Pflichtverstösse richtig ist, steht in Frage 3.
- **Prüfung an den 22 Beispielen** (`examples/*.xml`): Skript mit `python3 -I` und `xml.etree.ElementTree` (nur Zählung, gleiche Kindelement-Logik wie die Regel). Gezählt sind Objekte, die die Regel verletzen würden. Ausgangsmengen in den 22 Beispielen: 39 `ServiceJourney`, 38 `ServiceJourneyPattern` mit 206 `StopPointInJourneyPattern`, 36 `TimeDemandType` mit 136 `JourneyRunTime` und 25 `JourneyWaitTime`, 121 `TimingLink`, 5 `JourneyPart`. Wo die Spalte „Verstösse“ „0“ nennt, hält sich jedes Objekt der 22 Beispiele an die Regel; das stützt die Lesart der Regel.
- **Umfang:** 32 Einzelregeln (29 klar, 3 unklar). Das sind mehr als die im Plan geschätzten ~20, weil jede Pflicht-/Verbotsangabe einzeln steht (Rückverfolgbarkeit je Vorlagenzeile). Bei der Umsetzung lassen sich verwandte Regeln in einem Prüfschritt zusammenfassen (z. B. SJ-10/SJ-11, SJP-05/SJP-06, TL-01/TL-02), ohne Kennungen zu ändern.

## Pflichtelemente

| Kennung | Regel | Kontext | Prüfart | Schweregrad | Quelle | Status | Verstösse in den Beispielen |
|---|---|---|---|---|---|---|---|
| CH-SJ-01 | Eine `ServiceJourney` hat genau eine `AvailabilityConditionRef` unter `validityConditions`. | `ServiceJourney/validityConditions/AvailabilityConditionRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 13–19 (Z. 14 „mandatory“, Z. 18 „Only a single AvailabilityConditionRef is allowed“); `08_timetable.md` Z. 81; `b7ac158` | klar (Anwendungsbereich: Frage 1) | 3 von 39, nur Beispiel 17 (Rumpf-Fahrten) |
| CH-SJ-02 | Eine `ServiceJourney` hat das Element `ServiceAlteration`. | `ServiceJourney/ServiceAlteration` | Pflicht | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 87–92 (Z. 88 „mandatory“); `b7ac158` | klar (Frage 1) | 3 von 39, nur Beispiel 17 |
| CH-SJ-04 | Eine `ServiceJourney` hat genau eine `ServiceJourneyPatternRef`. | `ServiceJourney/ServiceJourneyPatternRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 99–102 (Z. 100 „mandatory“); `08_timetable.md` Z. 80, 84 („exactly one“); `b7ac158` | klar (Frage 1) | 3 von 39, nur Beispiel 17 |
| CH-SJ-05 | Eine `ServiceJourney` hat genau eine `TimeDemandTypeRef`. | `ServiceJourney/TimeDemandTypeRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 103–106 (Z. 104 „mandatory“, Z. 105 „only one TimeDemandType per ServiceJourney“); `08_timetable.md` Z. 84; `b7ac158` | klar (Frage 1) | 3 von 39, nur Beispiel 17 |
| CH-SJ-06 | Eine `ServiceJourney` hat mindestens eine `TrainNumberRef` unter `trainNumbers`. | `ServiceJourney/trainNumbers/TrainNumberRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 117–122 (Z. 118 und 120 „mandatory“); `b7ac158` | klar (Frage 1) | 3 von 39, nur Beispiel 17 |
| CH-SJ-07 | Eine `ServiceJourney` hat eine `TypeOfProductCategoryRef`. | `ServiceJourney/TypeOfProductCategoryRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 59–62 (Z. 60 „mandatory“); `b7ac158` | klar (Frage 1) | 3 von 39, nur Beispiel 17 |
| CH-SJ-08 | Eine `ServiceJourney` hat eine `DepartureTime` (nur „expected“, deshalb Hinweis). | `ServiceJourney/DepartureTime` | Pflicht | ℹ Hinweis | `templates/ServiceJourney.xml` Z. 93 („expected“); `08_timetable.md` Z. 95; `b7ac158` | klar (Frage 1) | 3 von 39, nur Beispiel 17 |
| CH-SJP-01 | Ein `ServiceJourneyPattern` hat unter `RouteView` eine `LineRef`. | `ServiceJourneyPattern/RouteView/LineRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 15–19 (Z. 16 und 18 „mandatory“); `08_timetable.md` Z. 88; `b7ac158` | klar | 0 von 38 |
| CH-SJP-02 | Ein `ServiceJourneyPattern` hat eine `DirectionType`. | `ServiceJourneyPattern/DirectionType` | Pflicht | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 21 („mandatory“); `b7ac158` | klar | 0 von 38 |
| CH-SJP-03 | Ein `ServiceJourneyPattern` hat `pointsInSequence` mit mindestens einem `StopPointInJourneyPattern`. | `ServiceJourneyPattern/pointsInSequence/StopPointInJourneyPattern` | Pflicht | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 22–25 (Z. 23 und 25 „mandatory“); `08_timetable.md` Z. 95; `b7ac158` | klar | 0 von 38 |
| CH-SJP-04 | Jeder `StopPointInJourneyPattern` hat eine `ScheduledStopPointRef`. | `StopPointInJourneyPattern/ScheduledStopPointRef` | Pflicht | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 26–28 (Z. 27 „mandatory“); `b7ac158` | klar | 0 von 206 |
| CH-SJP-05 | Jeder `StopPointInJourneyPattern` hat `ForAlighting`. | `StopPointInJourneyPattern/ForAlighting` | Pflicht | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 29 („mandatory“); `b7ac158` | klar | 0 von 206 |
| CH-SJP-06 | Jeder `StopPointInJourneyPattern` hat `ForBoarding`. | `StopPointInJourneyPattern/ForBoarding` | Pflicht | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 30 („mandatory“); `b7ac158` | klar | 0 von 206 |
| CH-SJP-08 | Ein `ServiceJourneyPattern` hat einen `ServiceJourneyPatternType` (nur „expected“). | `ServiceJourneyPattern/ServiceJourneyPatternType` | Pflicht | ℹ Hinweis (Vorschlag: nicht prüfen) | `templates/ServiceJourneyPattern.xml` Z. 70 („expected“); `b7ac158` | **unklar** (Frage 2) | 26 von 38 in 15 von 22 Beispielen |
| CH-TDT-01 | Ein `TimeDemandType` hat unter `runTimes` mindestens eine `JourneyRunTime` (nur „expected“). | `TimeDemandType/runTimes/JourneyRunTime` | Pflicht | ℹ Hinweis | `templates/TimeDemandType.xml` Z. 61–65 (Z. 62 und 65 „expected“); `b7ac158` | klar | 0 von 36 |
| CH-TDT-02 | Jede `JourneyRunTime` hat eine `TimingLinkRef`. | `JourneyRunTime/TimingLinkRef` | Pflicht | ⚠ Fehler | `templates/TimeDemandType.xml` Z. 66–69 (Z. 67 „mandatory“); `08_timetable.md` Z. 96; `b7ac158` | klar | 0 von 136 |
| CH-TDT-03 | Jede `JourneyRunTime` hat eine `RunTime`. | `JourneyRunTime/RunTime` | Pflicht | ⚠ Fehler | `templates/TimeDemandType.xml` Z. 70 („mandatory“); `b7ac158` | klar | 0 von 136 |
| CH-TDT-04 | Jede `JourneyWaitTime` hat eine `WaitTime`. | `JourneyWaitTime/WaitTime` | Pflicht | ⚠ Fehler | `templates/TimeDemandType.xml` Z. 83 („mandatory“); `b7ac158` | klar | 0 von 25 |
| CH-TDT-05 | Jede `JourneyWaitTime` nennt den Halt mit `ScheduledStopPointRef`, bei mehrfachem Besuch mit `StopPointInJourneyPatternRef` oder (Auswahl) mit `TimingPointRef` (nur „expected“). | `JourneyWaitTime/(ScheduledStopPointRef \| StopPointInJourneyPatternRef \| TimingPointRef)` | Pflicht | ℹ Hinweis | `templates/TimeDemandType.xml` Z. 79–82 (Z. 80 „expected“, Z. 81 Auswahl); `08_timetable.md` Z. 97; `b7ac158` | klar | 0 von 25 |
| CH-TL-01 | Jeder `TimingLink` hat eine `FromPointRef`. | `TimingLink/FromPointRef` | Pflicht | ⚠ Fehler | `templates/TimingLink.xml` Z. 56–60 (Z. 57 „mandatory“); `b7ac158` | klar | 0 von 121 |
| CH-TL-02 | Jeder `TimingLink` hat eine `ToPointRef`. | `TimingLink/ToPointRef` | Pflicht | ⚠ Fehler | `templates/TimingLink.xml` Z. 61–65 (Z. 62 „mandatory“); `b7ac158` | klar | 0 von 121 |
| CH-SJ-16 | Eine `ServiceJourney` hat unter `privateCodes` einen `PrivateCode` mit `type="sjyid"` (und `type="rn"`), „wenn vorhanden“. | `ServiceJourney/privateCodes/PrivateCode[@type]` | Pflicht | ℹ Hinweis (Vorschlag: nicht prüfen) | `templates/ServiceJourney.xml` Z. 35–49 (Z. 36 und 38 „expected“, Z. 40 „Mandatory if available“); `08_timetable.md` Z. 83, 89; `b7ac158` | **unklar** (Frage 4) | `sjyid` fehlt bei 8 von 39 in 6 von 22 Beispielen (01, 10, 11, 14, 20, 21) |

## Verbotene Elemente

| Kennung | Regel | Kontext | Prüfart | Schweregrad | Quelle | Status | Verstösse in den Beispielen |
|---|---|---|---|---|---|---|---|
| CH-SJ-09 | Eine `ServiceJourney` hat kein `PrivateCode` direkt als Kind (ersetzt durch `privateCodes/PrivateCode`). | `ServiceJourney/PrivateCode` | verboten | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 50–54 (Z. 51 „forbidden“, Z. 52 „Replaced by privateCodes“); `08_timetable.md` Z. 89; `b7ac158` | klar (Rest: Frage 4) | 0 von 39 |
| CH-SJ-10 | Eine `ServiceJourney` hat keine `LineRef` (steht im `ServiceJourneyPattern`). | `ServiceJourney/LineRef` | verboten | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 112–115 (Z. 113 „forbidden“); `08_timetable.md` Z. 88; `b7ac158` | klar | 0 von 39 |
| CH-SJ-11 | Eine `ServiceJourney` hat kein `DirectionType` (steht im `ServiceJourneyPattern`). | `ServiceJourney/DirectionType` | verboten | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 116 („forbidden“); `b7ac158` | klar | 0 von 39 |
| CH-SJ-12 | Eine `ServiceJourney` hat keine `passingTimes`. | `ServiceJourney/passingTimes` | verboten | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 129–134 (Z. 130 „forbidden“); `b7ac158` | klar | 0 von 39 |
| CH-SJ-13 | Eine `ServiceJourney` hat keine `calls`. | `ServiceJourney/calls` | verboten | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 145–153 (Z. 146 „forbidden“); `b7ac158` | klar | 0 von 39 |
| CH-SJ-14 | Die Fahrt-ID `sjyid` steht nicht in der `keyList` (sondern in `privateCodes`). | `ServiceJourney/keyList/KeyValue/Key` mit Wert `sjyid` | verboten | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 21–23 (Z. 23 „We don't use it for sjyid!“); `08_timetable.md` Z. 89; `b7ac158` | klar | 0 von 39 |

## Erlaubte Werte

| Kennung | Regel | Kontext | Prüfart | Schweregrad | Quelle | Status | Verstösse in den Beispielen |
|---|---|---|---|---|---|---|---|
| CH-SJ-03 | `ServiceAlteration` hat den Wert `planned`; andere Werte sind nicht erlaubt. | `ServiceJourney/ServiceAlteration` | Wert | ⚠ Fehler | `templates/ServiceJourney.xml` Z. 89–91 (Z. 89 „ch-allowed-enums: planned“, Z. 90 „Only the value planned is allowed“); `b7ac158` | klar | 0 von 36 vorhandenen |
| CH-SJ-15 | `TypeOfServiceRef` verweist auf `ch:1:TypeOfService:1`. | `ServiceJourney/TypeOfServiceRef/@ref` | Wert | ℹ Hinweis (Vorschlag) | `templates/ServiceJourney.xml` Z. 63–66 (Z. 65 „Should always be“; Element optional); `08_timetable.md` Z. 199 („We only use“); `b7ac158` | klar | 0 von 39 |
| CH-SJP-07 | `ServiceJourneyPatternType` hat den Wert `passenger`. | `ServiceJourneyPattern/ServiceJourneyPatternType` | Wert | ⚠ Fehler | `templates/ServiceJourneyPattern.xml` Z. 70 (`ch-allowed-enums: passenger`, „We currently only allow passenger“); `b7ac158` | klar | 0 von 12 vorhandenen |
| CH-JP-01 | `PurposeOfJourneyPartitionRef` einer `JourneyPart` verweist auf `ch:1:PurposeOfJourneyPartition:FacilityChange` oder `…:TypeOfProductCategoryChange`. | `JourneyPart/PurposeOfJourneyPartitionRef/@ref` | Wert | △ Warnung (Vorschlag) | `templates/JourneyPart.xml` Z. 86–90 (Z. 88 `ch-allowed-enums`, Z. 89 „Only two values are allowed“); `uc05_journey_parts.md` Z. 24, 64; `b7ac158` | **unklar** (Frage 5) | 3 von 5 (Beispiel 21, `DirectCarriage`) |

## Unklare Regeln

Fragen werden einzeln geklärt. Bis zur Antwort wird die betroffene Regel nicht umgesetzt. Das Ergebnis kommt in [decisions.md](decisions.md).

### Frage 1: Gelten die Regeln für `ServiceJourney` auch in `INTERCHANGE`-Dateien?

Betrifft CH-SJ-01, -02, -04, -05, -06, -07, -08 (jeweils 3 Verstösse, nur Beispiel 17).

- **Lesart A (jede `ServiceJourney` einer Datei):** Die Vorlage nennt keinen Dateityp. Dann ergäben die drei Rumpf-`ServiceJourney` in Beispiel 17 (`examples/17_NeTEx_CH_INTERCHANGE.xml` Z. 27–41, jede nur mit `privateCodes/PrivateCode type="sjyid"`) zusammen 21 Befunde in einem Guide-Beispiel.
- **Lesart B (nur in `NETWORK_OFFER`):** Der Guide trennt die Dateitypen: `NETWORK_OFFER` ist „lines, routes, timetables“, `INTERCHANGE` „interchanges, Durchbindungen“ (`02_files.md` Z. 77–78); die `ServiceJourney` in `INTERCHANGE` dienen nur als Ziel der `ServiceJourneyInterchange` (Beispiel 17 Z. 43 ff.). Die Vorlage beschreibt die vollständige Fahrt.
- **Empfehlung: B.** Die Regeln gelten für Dateien vom Typ `NETWORK_OFFER`; der Dateityp kommt aus dem Dateinamen (`02_files.md` Z. 160–165, „Type of file“). Ist der Typ nicht erkennbar (Guide-Beispiele tragen ihn teils nicht im Namen), gelten die Regeln für alle Fahrten, ausser sie enthalten nichts ausser `privateCodes`; das wird als ℹ Hinweis „Rumpf-Fahrt, Fahrplanregeln nicht angewandt“ gezeigt, nicht still übergangen.

### Frage 2: Soll das Fehlen von `ServiceJourneyPatternType` gemeldet werden (CH-SJP-08)?

- **Lesart A (Fehlen melden):** Vorlage Z. 70 nennt `ch-usage: expected`; fehlt es, weicht die Datei vom erwarteten Normalfall ab. Hinweis.
- **Lesart B (Fehlen ist normal):** 26 von 38 Fahrtmustern in 15 von 22 Beispielen haben kein `ServiceJourneyPatternType`; alle 12 vorhandenen haben `passenger` (CH-SJP-07 ohne Verstoss). Der Guide-eigene Normalfall wäre damit „Hinweis“. Nach `03_xml_modelling.md` Z. 242 ist „expected“ ausdrücklich schwächer als „mandatory“.
- **Empfehlung: B.** Nur den Wert prüfen (CH-SJP-07), das Fehlen nicht melden. CH-SJP-08 wird nicht umgesetzt; die Zeile bleibt als Beleg stehen.

### Frage 3: Schweregrade der Kernregeln

Betrifft alle Regeln, besonders „expected“ (CH-SJ-08, CH-SJP-08, CH-TDT-01, CH-TDT-05).

- **Lesart A (Pflicht/Verbot = ⚠ Fehler, „expected“ = ℹ Hinweis):** Entspricht der Wortwahl der Vorlagen („mandatory“, „forbidden“, „Only the value planned is allowed“). Alle Guide-Beispiele halten die Pflicht- und Verbotsregeln ein (ausser Rumpf-Fahrten, Frage 1), eine strenge Stufe erzeugt dort also keinen Lärm.
- **Lesart B (alles △ Warnung, solange der Guide Entwurf ist):** Das Profil ist ein Entwurf (`2.0`, Branch `next`), „Fehler“ könnte zu streng wirken; die XSD-Fehler sind ohnehin die harte Stufe.
- **Empfehlung: A.** Pflichtverstösse und verbotene Elemente = ⚠ Fehler, Werte ausserhalb der Aufzählung = ⚠ Fehler, „expected“ und „sollte“ = ℹ Hinweis, das Ergebnis heisst weiterhin „geprüft gegen Entwurf `b7ac158`“. Die Schweregrade stehen in der Hilfeseite und lassen sich später je Regel in einer Konfiguration ändern.

### Frage 4: `PrivateCode` direkt unter `ServiceJourney` oder `privateCodes/PrivateCode`; Pflicht für `sjyid`

Die Prüfung am Vorlagentext ergibt für das Verbot **keinen Widerspruch**; offen bleibt nur die Pflicht (CH-SJ-16).

- **Verbot (CH-SJ-09), Lesart A:** Ein `PrivateCode` direkt als Kind der `ServiceJourney` ist verboten: Vorlage Z. 50–54 („forbidden“, „Replaced by `<privateCodes>`-`<PrivateCode>`“), `templates/TemplateServiceJourney.xml` Z. 24 („Replaces the single PrivateCode“), `08_timetable.md` Z. 89. Alle 39 Fahrten der Beispiele halten das ein.
- **Lesart B (nur der Typ `sjyid` ist gemeint):** Andere Objekte verwenden `PrivateCode` direkt (z. B. `ResponsibilitySet`, Beispiel 01 Z. 27; `Notice` „expected“, `templates/Notice.xml` Z. 43; `Operator` und `DestinationDisplay` „forbidden“, `templates/Operator.xml` Z. 28). Die Vorlage der `ServiceJourney` schränkt aber nicht auf einen Typ ein. Die Vorlage `templates/JourneyPart.xml` Z. 29 zeigt allerdings eine eingebettete `ServiceJourney` mit direktem `<PrivateCode>1</PrivateCode>` (ohne `ch-usage`-Kommentare); sie ist ein Ausschnitt für die `JourneyPart`, widerspricht aber dem Verbot formal.
- **Pflicht (CH-SJ-16):** Z. 36/38 sagen „expected“, Z. 40 sagt „Mandatory if available for the following types: sjyid and rn“. „Wenn vorhanden“ lässt sich aus der Datei nicht prüfen (das Tool kann nicht wissen, ob eine `sjyid` existiert); in 8 von 39 Fahrten fehlt sie (Beispiele 01, 10, 11, 14, 20, 21), nach `08_timetable.md` Z. 83 darf das bei Fremdfahrten sein.
- **Empfehlung:** CH-SJ-09 (Vorlage `ServiceJourney.xml` geht der Ausschnitt in `JourneyPart.xml` vor) und CH-SJ-14 als Regeln umsetzen (Lesart A). CH-SJ-16 nicht prüfen; stattdessen genügt die Fahrtansicht, die `sjyid` zeigt, wenn sie da ist. Falls der Benutzer doch einen Hinweis will: ℹ Hinweis „keine `sjyid` angegeben“.

### Frage 5: Erlaubte Werte von `PurposeOfJourneyPartitionRef` (CH-JP-01)

- **Lesart A (zwei Werte, wie in der Vorlage):** `ch-allowed-enums` nennt `ch:1:PurposeOfJouryneyPartition:TypeOfProductCategoryChange` und `ch:1:PurposeOfJourneyPartition:FacilityChange` (`templates/JourneyPart.xml` Z. 88); „Only two values are allowed“ (Z. 89). Der erste Wert enthält einen offensichtlichen Tippfehler („Jouryney“), der ebenso in `uc05_journey_parts.md` Z. 64 steht; die Notiz Z. 89 nennt zusätzlich `TrainNumberChange`, `uc05` Z. 68 sagt dazu „NOT USED“.
- **Lesart B (Beispiel gilt):** Beispiel 21 (Kurswagen) verwendet `ch:1:PurposeOfJourneyPartition:DirectCarriage` in 3 von 5 `JourneyPart` (`examples/21_NeTEx_CH_Kurswagen_Zuerich_Bremen.xml`); `uc08_kurswagen.md` Z. 43 sagt dagegen, `JourneyPart` werde für Kurswagen nicht verwendet (siehe [mapping.md](mapping.md) P2, [assumptions.md](assumptions.md)). Wäre der Wert gewollt, fehlte er in der Aufzählung.
- **Empfehlung:** Die Regel nur als △ Warnung umsetzen: erlaubt sind `…:FacilityChange` und `…:TypeOfProductCategoryChange` (die Schreibweise mit „Jouryney“ wird als Tippfehler im Guide nicht akzeptiert, sondern die Warnung nennt beide Schreibweisen und verweist auf Zeile 88/64). Beispiel 21 ergibt damit 3 Warnungen, die die Widersprüche im Guide sichtbar machen. Zusätzlich dem Guide melden, falls der Benutzer das möchte.

### Frage 6: Diagnosen der Fahrtansicht im Beispielstatus (Entscheid (16) aus Phase 3)

Heute zählen die Befunde der Fahrtansicht (Art `projection`: nicht berechenbare Zeit, Standardwerte, Von-/Nach-Punkt-Hinweis, `order`-Abweichung, Nacht der Zeitumstellung, nicht zugeordnete Hinweiszuweisungen, `ValidDayBits` ohne Bezug zum Zeitraum, Zeit der `JourneyPart` weicht ab) weder in `diagnosticCounts` noch in den Beispielstatus ([decisions.md](decisions.md) „Umsetzung Phase 3“ (3) und Offene Punkte 12–17 (16)). Mit Phase 4 kommen XSD-Prüfung, `general_rules.sch` und die Kernregeln dazu.

- **Lesart A (getrennt lassen):** Beispielstatus und Zählung gelten für die **Prüfung der Datei** (XSD, `general_rules.sch`, Kernregeln, Referenzen). Die Fahrtansicht zeigt ihre Befunde bei der Fahrt. Vorteil: der Status bleibt stabil und erklärbar; 15 von 22 Beispielen hätten sonst wegen der Länge von `ValidDayBits` eine △ Warnung ([mapping.md](mapping.md) B6), 11 wegen `order` (121 Verstösse, [decisions.md](decisions.md) „Prüfergebnisse Guide-Beispiele“); fast jedes Beispiel wäre „mit Meldungen“.
- **Lesart B (alles zählt):** Der Status zeigt dann alles, was am Beispiel auffällig ist, auch das Berechnungsergebnis. Nachteil: der Status würde bei jedem Abruf einer Fahrt wechseln (Befunde entstehen erst beim Abruf), `order` würde doppelt gezählt (Fahrtansicht und Schematron-Regel d), und die Status-Aussage „ohne Meldungen“ wäre kaum noch erreichbar.
- **Empfehlung: A, mit zwei Ergänzungen:** (1) Prüfungen, die Phase 4 selbst ausführt (XSD, `general_rules.sch` einschliesslich `order`, Kernregeln), zählen in den Beispielstatus; der `order`-Befund der Fahrtansicht bleibt als Hinweis bei der Fahrt, zählt aber nicht zusätzlich. (2) Die Dateiübersicht zeigt je Datei eine getrennte Zeile „Befunde der Fahrtansicht: n“ nur auf Anfrage (nicht im Status), damit nichts verborgen ist. Entscheid anschliessend in `decisions.md` eintragen und (16) ersetzen.

## Bewusst nicht als Kernregel

| Was | Warum nicht |
|---|---|
| Freie Texte, z. B. `TypeOfName` mit Wert `offical` (Beispiel 01 Z. 99 ff., vermutlich Tippfehler) | Freier Text ohne Aufzählung im Guide, kein Regelverstoss ([UMSETZUNGSPLAN.md](../UMSETZUNGSPLAN.md) Abschnitt 8). |
| `ch-usage: expected` ohne Pflichtcharakter in der Praxis: `VehicleTypeRef` (`templates/ServiceJourney.xml` Z. 107–111; fehlt in 37 von 39 Fahrten), `Destination` (Z. 123–128; fehlt in 32 von 39), `JourneyPart` (Z. 139) | „expected“ wäre in fast allen Beispielen ein Hinweis; kein Nutzen, Lärm. Die Fahrtansicht zeigt, was vorhanden ist. |
| `ch-usage: optional`, `ignored`, `ch-note: Currently not available` (`OccupancyView`, `BookingArrangement` in `ServiceJourneyPattern.xml` Z. 50–56, `JourneyPartCoupleRef` in `JourneyPart.xml` Z. 66–69) | Keine Aussage „Pflicht“ oder „verboten“; „ignored“ heisst, der Guide liest es nicht, nicht, dass es fehlerhaft wäre. |
| `StopUse` („All values possible“, `ServiceJourneyPattern.xml` Z. 36), `TransportMode` (optional) | Keine Einschränkung; Bedeutung der Codes aus der Mappingtabelle ([mapping.md](mapping.md) E2, V2). |
| `DepartureDayOffset` (optional; „Could also be negative“) | Keine Regel; Standardwert 0 ist als Anzeige umgesetzt ([mapping.md](mapping.md) M2). |
| Wertlisten aus der Mappingtabelle („Relevant elements are defined in the mapping excel“, z. B. `TypeOfProductCategoryRef`, `ServiceFacilitySet`) | Externe Liste mit eigener Pflege; wird bei Bedarf als eigener Prüfschritt mit Blatt, Zeile und Stand aufgenommen, nicht aus der Vorlage geraten. |
| Weitere Pflichtangaben der `JourneyPart` (`FromStopPointRef`, `StartTime`, `EndTime`, `ToStopPointRef` „expected“, `templates/JourneyPart.xml` Z. 74–85), `Description` und `Name` | Ausserhalb von `ServiceJourney`, `ServiceJourneyPattern`, `TimeDemandType`; kommen mit den übrigen ~330 Profilregeln. |
| `TemplateServiceJourney` (Beispiel 12, 3 Objekte), `DatedServiceJourney` (nicht verwendet) | Eigene Vorlage `templates/TemplateServiceJourney.xml` mit eigenen Angaben; wird mit der Takt-Ansicht ([open-points.md](open-points.md), Zurückgestellt) behandelt. |
| Zusammenhänge: Verweis zeigt auf vorhandenes Objekt; `TimeDemandType` hat eine `RunTime` zu jedem `TimingLink` der Haltefolge; `DepartureTime` und Fahrzeiten ergeben eine plausible Fahrt; Länge von `ValidDayBits`; `id` einer Fahrt beginnt mit der `sjyid` (`08_timetable.md` Z. 83) | Verweise prüft die Referenzdiagnose (Phase 2); Berechnung und Betriebstage die Fahrtansicht (Phase 3, [mapping.md](mapping.md) Z4, Z7, B6). Keine doppelte Prüfung. |
| Attributlisten (`ch-attrs`), Formate (`hh:mm:ss`, Dauer `PT5M`), `order`-Attribut | Formate prüft die XSD; `order` die Regel d in `general_rules.sch`. |
| Verschachtelte Pflicht in nicht vorhandenen Elternelementen (z. B. `ForBoarding` ohne `StopPointInJourneyPattern`) | Eine Pflicht gilt nur, wenn das Elternelement vorhanden ist. |

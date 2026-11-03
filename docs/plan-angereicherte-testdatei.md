# Plan: angereicherte Testdatei aus Guide-Beispielen

Grundlage: Guide-Commit `b7ac158` (`../netexRealisationGuideSwitzerland`, Branch `next`), Stand 03.11.2026. Umsetzung zurückgestellt; eine spätere Sitzung kann den Plan ohne Vorwissen ausführen.

## Ziel und Entscheide

- Entscheide in [decisions.md](decisions.md): 02.11.2026 (Zweck, Weg, Ablage als Ausnahme) und 03.11.2026 (Kennzeichnung, Variante a).
- Zweck: realistische Fahrten mit möglichst vielen Angaben für die Fahrtansicht. 3–5 Fahrten, eine Datei in `fixtures/`.
- Lieferdaten aus `../netex-files/` werden nicht verwendet. Guide-Dateien nur lesen, nicht ändern.

## Ausgangslage Beispiel 13

`src/examples/13_NeTEx_CH_Bern_Spiez_Zweisimmen_TimeDemandType_Quay_Change.xml` (719 Zeilen, `ParticipantRef` `TUXALP`, Betreiber BLS `ch:1:sboid:100015`):

- `ServiceJourney:1` RE 4175 Bern - Thun - Spiez (ab 14:39), `:2` R 6829 Spiez - Zweisimmen (ab 08:30), `:3` RE 4179 Spiez - Frutigen - Brig (ab 15:12). Flügelung in Spiez, Gleiswechsel (3 nach 5).
- Frames: `CompositeFrame` mit `ResourceFrame`, `SiteFrame`, `ServiceCalendarFrame` (`AvailabilityCondition:1`, `ValidDayBits`), `ServiceFrame` (Linien, 3 `ServiceJourneyPattern`, 3 `TimeDemandType`, ein `DestinationDisplay`, `TypeOfProductCategory` R/RE), `TimetableFrame` (Fahrten, 3 `TrainNumber`, 2 `ServiceJourneyInterchange` SJ1-SJ2 und SJ1-SJ3).
- Nicht enthalten: `JourneyPart`, `ServiceFacilitySet`, `NoticeAssignment`, Zielwechsel, Zugnummernwechsel, Formation.

## Bausteine

| Baustein | Quellbeispiel | Konkrete Elemente | Zielfahrt | Nötige Anpassungen |
|---|---|---|---|---|
| Angebote ganze Fahrt und Teilstrecke, einzelne Tage | 08 (Bern - Olten - Zürich HB, IC 703) | `ServiceFacilitySet` (`bistro-open`, `generated-1`), `JourneyPart` mit `PurposeOfJourneyPartition` (`ValueSet` in `ResourceFrame`), `FromStopPointInJourneyPatternRef`/`ToStop…`, `AvailabilityCondition` (`ValidDayBits`) mit Ausnahmetagen, `Notice`/`NoticeAssignment` | SJ1 (Bern - Spiez, Teilstrecke Bern - Thun) | IDs eindeutig machen (Quelle nutzt `generated-part-1`, `na-1`); Halte auf `ServiceJourneyPattern:1` umstellen; eigene `AvailabilityCondition` mit gleicher Länge der `ValidDayBits` wie die Datei |
| Zielwechsel | 10 (BLS Bern - Luzern, bis Wolhusen) | zweites `DestinationDisplay` (`DD_WOLHUSEN`), Wechsel in `StopPointInJourneyPattern`, `DestinationDisplayRef` an der Fahrt, `Notice` Bauarbeiten | SJ3 (Spiez - Frutigen - Brig): Anzeige wechselt ab Frutigen | Zielnamen und Halte aus Beispiel 13 verwenden; Notiztext neu (nichts erfinden, was nach echter Auskunft aussieht, siehe offene Fragen) |
| Zugnummernwechsel | 11 (Bern - Wolhusen / Wolhusen - Luzern) | zwei `TrainNumber`, zwei `ServiceJourney` mit `ServiceJourneyInterchange` (`StaySeated`) | zusätzliche Fahrt oder SJ2 | siehe offene Fragen (Strecke Spiez - Zweisimmen hat nur 2 Halte) |
| Formation | 20 (Interlaken - Spiez, Entwurf) | `CompoundTrain`, `Train`, `TrainInCompoundTrain`, `TrainComponent`, `TrainElement`, `ServiceFacilitySet` (`wheelchairspace`, `bikehooks`, `strollerplattform`, `nf`), `CompoundTrainRef` in der Fahrt | SJ1 | Strecke und Linie von Beispiel 20 (Interlaken) passen nicht zu Bern - Spiez; Fahrzeug-IDs und Verweise übernehmen. Guide-README: nur Entwurf |
| Anschluss | 17 (INTERCHANGE), 13 | `ServiceJourneyInterchange` mit `StaySeated`, `Planned`, `Guaranteed`, `ChangeWithinVehicle` | SJ1 nach SJ2/SJ3 | in 13 bereits vorhanden (beide Anschlüsse in Spiez); 17 liefert nichts Neues, nur prüfen, ob Felder fehlen |
| Hinweise | 02, 03, 15 | `Notice`/`NoticeAssignment` (z. B. `A__GR` Gruppenreservation), Zuordnung zu Fahrt oder `JourneyPattern`-Abschnitt | SJ2, SJ3 | `TypeOfNotice`-Verweise in `ResourceFrame` prüfen |
| Verkehrstage | 03, 15 | `DayType` (Weihnachten), mehrere `AvailabilityCondition`, Ausnahmetage in `ValidDayBits` | SJ2, SJ3 | Bitfolge passt zu `FromDate`/`ToDate` |
| Bedarfshalt | 03, 02 | `RequestStop`, `StopUse` im `StopPointInJourneyPattern` | SJ2 (Zwischenhalt, falls vorhanden) | Quelle nutzt `RequestStop` false/`StopUse` access; Bedarfshalt (`true`) in 03 nicht belegt, im Guide-Template prüfen |
| optional Fahrt 4: Bus | 03 (Linie 803 Nyon) | `TransportMode` bus, `VehicleType`, 2 `ServiceJourney`, `DayType` | neu | eigene Linie, Halte, `SiteFrame`-Einträge ergänzen; grosser Zusatz |
| optional Fahrt 5: Taktfahrt | 12 (Frequenzlinie) | `TemplateServiceJourney`, `HeadwayJourneyGroup`, `AvailabilityCondition` | neu | prüfen, ob die Fahrtansicht `TemplateServiceJourney` unterstützt (sonst nutzlos) |

Vorlagen in `../netexRealisationGuideSwitzerland/src/templates/` (z. B. `JourneyPart.xml`, `ServiceFacilitySet.xml`, `NoticeAssignment.xml`, `CompoundTrain.xml`, `DestinationDisplay.xml`) zur Kontrolle der Elementreihenfolge und Pflichtfelder lesen.

## Vorgehen

1. Beispiel 13 nach `fixtures/ch20_enriched_bern_spiez.xml` kopieren (Name beim Start bestätigen). Kopfkommentar „SYNTHETISCHE TESTDATEN, abgeleitet aus Guide-Beispielen <Liste>, Guide-Commit <Hash>“ setzen, `ParticipantRef` auf `SYNTHETIC` ändern. Ohne beides schlägt `tests/test_fixtures.py` fehl.
2. Bausteine einzeln einbauen, nach jedem XSD prüfen (lxml gegen `../netexRealisationGuideSwitzerland/xsd/xsd/NeTEx_publication.xsd`, wie im README von `fixtures/` beschrieben).
3. Gesamtprüfung wie im Tool: `ValidationEngine.validate(dataset)` (`app/core/validation/engine.py`): XSD, `general_rules.sch` und Schweizer Kernregeln (`core_rules.check_core_rules`). Muster: `validate_fixture` und `problems` in `tests/core/validation/test_engine.py`. Ziel: keine Diagnosen der Kategorien XSD und PROFILE_RULE.
4. Datei im Tool öffnen (`scripts/start.py`), Fahrtansicht je Fahrt sichten: Angaben sichtbar, Herkunft (Frame, Zeile) stimmt, Flügelung und Gleiswechsel unverändert.
5. Test ergänzen: Datei lädt, keine Fehler (nach Muster `test_other_valid_fixtures_have_no_xsd_errors` in `tests/core/validation/test_engine.py`, dort die Liste erweitern) und die wichtigsten Angaben in der Fahrtansicht (Muster `tests/core/projection/test_journey_view.py`, `fixture_view`).
6. `fixtures/README.md` nachführen: Tabellenzeile, Abweichung von der `SYN`-Konvention (Einleitungsabsatz sagt bisher „keine Kopien von Guide-Dateien“, anpassen), Herkunft und Guide-Commit. `test_fixture_is_documented` verlangt den Dateinamen in Backticks.
7. Hilfeseite ist nicht betroffen, solange keine Funktion geändert wird (prüfen, `tests/test_help_texts.py`). `uv run python scripts/check.py`, Commit, kein Push.

## Offene Fragen beim Start (einzeln mit dem Benutzer klären)

1. Dateiname (Vorschlag `ch20_enriched_bern_spiez.xml`).
2. Kommen Fahrt 4 (Bus) und Fahrt 5 (Taktfahrt) dazu? Fahrt 5 nur sinnvoll, wenn die Fahrtansicht `TemplateServiceJourney` anzeigt.
3. Wird die Formation (Beispiel 20, nur Entwurf) aufgenommen?
4. Fachlich Unpassendes aus der Prüfung:
   - Zielwechsel (10) und Zugnummernwechsel (11) stammen von Bern - Luzern; in Beispiel 13 gibt es keinen vergleichbaren Anlass (Bauarbeiten). Konstruierter Anlass nötig; Notiztext wäre erfunden.
   - Zugnummernwechsel braucht eine zweite Fahrt am selben Zug; Spiez - Zweisimmen (SJ2) hat nur 2 Halte.
   - Formation (20) gehört zu Interlaken - Spiez, nicht Bern - Spiez; Linie, Halte, Fahrzeuge müssten angepasst werden.
   - Anschluss (17): in 13 schon vorhanden, nichts hinzuzufügen.
   - `R` (Regio, SJ2) mit Bistro/Gruppenreservation (08, 15) ist fachlich fraglich; Angebote besser an `RE` (SJ1, SJ3).
   - Bedarfshalt: kein Beispiel mit `RequestStop` true gefunden, nur false.
   - Zuggattung: 08 ist IC, 13 sind R/RE; Angebote mit Bistro bei IC üblich, bei RE zu klären.

## Risiken und Hinweise

- ID-Konsistenz über Frames: jede neue ID eindeutig, jede Referenz mit passendem `version`, `ResourceFrame`-Objekte (`ValueSet`, `TypeOfNotice`) vor Verwendung definiert.
- Flügelzug (SJ1 mit SJ2/SJ3) nicht stören: `JourneyPart` nur mit gültigem `JourneyPatternRef`, Von-/Bis-Halt innerhalb der Fahrt.
- Keine Lieferdaten aus `../netex-files/` verwenden, keine Namen und Zeiten erfinden, die wie echte Auskunft wirken.
- Lizenz des Guide-Repos ungeklärt (keine Lizenzdatei, Stand `b7ac158`): nicht pushen, bevor geklärt (Vorgabe in `CLAUDE.md`: nichts hochladen ohne Auftrag).
- Aufwand ca. ½–1 Tag. Umsetzung an einen Sonnet-Subagenten delegierbar, Prüfung (Schritte 3 und 4) durch den Hauptagenten.

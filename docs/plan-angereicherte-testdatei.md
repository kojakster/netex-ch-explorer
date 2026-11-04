# Plan: angereicherte Testdatei aus Guide-Beispielen

> **Status: unvollständig.** Die offenen Punkte unten müssen vor der Umsetzung mit dem Benutzer geklärt werden (einzeln, je Entscheid in [decisions.md](decisions.md)), damit die Fahrtansicht eine qualitativ gute, fachlich stimmige Datei zeigt. Erst danach ist der Plan umsetzbar.

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
| Angebote ganze Fahrt und Teilstrecke, einzelne Tage | 08 (Bern - Olten - Zürich HB, IC 703) | `ServiceFacilitySet` (`bistro-open`, `generated-1`), `JourneyPart` mit `PurposeOfJourneyPartition` (`ValueSet` in `ResourceFrame`), `FromStopPointInJourneyPatternRef`/`ToStop…`, `AvailabilityCondition` (`ValidDayBits`) mit Ausnahmetagen, `Notice`/`NoticeAssignment` | SJ1 (Bern - Spiez, Teilstrecke Bern - Thun) (Punkte 1, 6, 13) | IDs eindeutig machen (Quelle nutzt `generated-part-1`, `na-1`); Halte auf `ServiceJourneyPattern:1` umstellen; eigene `AvailabilityCondition` mit gleicher Länge der `ValidDayBits` wie die Datei |
| Zielwechsel (entfällt, Punkt 2) | 10 (BLS Bern - Luzern, bis Wolhusen) | zweites `DestinationDisplay` (`DD_WOLHUSEN`), Wechsel in `StopPointInJourneyPattern`, `DestinationDisplayRef` an der Fahrt, `Notice` Bauarbeiten | SJ3 (Spiez - Frutigen - Brig): Anzeige wechselt ab Frutigen (Punkte 1, 2, 14) | Zielnamen und Halte aus Beispiel 13 verwenden; Notiztext neu (nichts erfinden, was nach echter Auskunft aussieht, siehe offene Fragen) |
| Zugnummernwechsel | 11 (Bern - Wolhusen / Wolhusen - Luzern) | zwei `TrainNumber`, zwei `ServiceJourney` mit `ServiceJourneyInterchange` (`StaySeated`) | entfällt, in 13 vorhanden (Punkt 3) | siehe offene Fragen (Strecke Spiez - Zweisimmen hat nur 2 Halte) |
| Formation | 20 (Interlaken - Spiez, Entwurf) | `CompoundTrain`, `Train`, `TrainInCompoundTrain`, `TrainComponent`, `TrainElement`, `ServiceFacilitySet` (`wheelchairspace`, `bikehooks`, `strollerplattform`, `nf`), `CompoundTrainRef` in der Fahrt | SJ1 (Punkt 4) | Strecke und Linie von Beispiel 20 (Interlaken) passen nicht zu Bern - Spiez; Fahrzeug-IDs und Verweise übernehmen. Guide-README: nur Entwurf |
| Anschluss | 17 (INTERCHANGE), 13 | `ServiceJourneyInterchange` mit `StaySeated`, `Planned`, `Guaranteed`, `ChangeWithinVehicle` | SJ1 nach SJ2/SJ3 (Punkt 5) | in 13 bereits vorhanden (beide Anschlüsse in Spiez); 17 liefert nichts Neues, nur prüfen, ob Felder fehlen |
| Hinweise | 02, 03, 15 | `Notice`/`NoticeAssignment` (z. B. `A__GR` Gruppenreservation), Zuordnung zu Fahrt oder `JourneyPattern`-Abschnitt | SJ2, SJ3 (Punkte 1, 6, 14) | `TypeOfNotice`-Verweise in `ResourceFrame` prüfen |
| Verkehrstage | 03, 15 | `DayType` (Weihnachten), mehrere `AvailabilityCondition`, Ausnahmetage in `ValidDayBits` | SJ2, SJ3 (Punkt 15) | Bitfolge passt zu `FromDate`/`ToDate` |
| Bedarfshalt | 03, 02 | `RequestStop`, `StopUse` im `StopPointInJourneyPattern` | SJ2 (Zwischenhalt, falls vorhanden) (Punkt 7) | Quelle nutzt `RequestStop` false/`StopUse` access; Bedarfshalt (`true`) in 03 nicht belegt, im Guide-Template prüfen |
| optional Fahrt 4: Bus | 03 (Linie 803 Nyon) | `TransportMode` bus, `VehicleType`, 2 `ServiceJourney`, `DayType` | neu (Punkt 8) | eigene Linie, Halte, `SiteFrame`-Einträge ergänzen; grosser Zusatz |
| optional Fahrt 5: Taktfahrt | 12 (Frequenzlinie) | `TemplateServiceJourney`, `HeadwayJourneyGroup`, `AvailabilityCondition` | neu (Punkt 9) | prüfen, ob die Fahrtansicht `TemplateServiceJourney` unterstützt (sonst nutzlos) |

Vorlagen in `../netexRealisationGuideSwitzerland/src/templates/` (z. B. `JourneyPart.xml`, `ServiceFacilitySet.xml`, `NoticeAssignment.xml`, `CompoundTrain.xml`, `DestinationDisplay.xml`) zur Kontrolle der Elementreihenfolge und Pflichtfelder lesen.

## Vorgehen

1. Beispiel 13 nach `fixtures/ch20_enriched_bern_spiez.xml` kopieren (Name beim Start bestätigen). Kopfkommentar „SYNTHETISCHE TESTDATEN, abgeleitet aus Guide-Beispielen <Liste>, Guide-Commit <Hash>“ setzen, `ParticipantRef` auf `SYNTHETIC` ändern. Ohne beides schlägt `tests/test_fixtures.py` fehl.
2. Bausteine einzeln einbauen, nach jedem XSD prüfen (lxml gegen `../netexRealisationGuideSwitzerland/xsd/xsd/NeTEx_publication.xsd`, wie im README von `fixtures/` beschrieben).
3. Gesamtprüfung wie im Tool: `ValidationEngine.validate(dataset)` (`app/core/validation/engine.py`): XSD, `general_rules.sch` und Schweizer Kernregeln (`core_rules.check_core_rules`). Muster: `validate_fixture` und `problems` in `tests/core/validation/test_engine.py`. Ziel: keine Diagnosen der Kategorien XSD und PROFILE_RULE.
4. Datei im Tool öffnen (`scripts/start.py`), Fahrtansicht je Fahrt sichten: Angaben sichtbar, Herkunft (Frame, Zeile) stimmt, Flügelung und Gleiswechsel unverändert.
5. Test ergänzen: Datei lädt, keine Fehler (nach Muster `test_other_valid_fixtures_have_no_xsd_errors` in `tests/core/validation/test_engine.py`, dort die Liste erweitern) und die wichtigsten Angaben in der Fahrtansicht (Muster `tests/core/projection/test_journey_view.py`, `fixture_view`).
6. `fixtures/README.md` nachführen: Tabellenzeile, Abweichung von der `SYN`-Konvention (Einleitungsabsatz sagt bisher „keine Kopien von Guide-Dateien“, anpassen), Herkunft und Guide-Commit. `test_fixture_is_documented` verlangt den Dateinamen in Backticks.
7. Hilfeseite ist nicht betroffen, solange keine Funktion geändert wird (prüfen, `tests/test_help_texts.py`). `uv run python scripts/check.py`, Commit, kein Push.

## Offene Punkte (vor der Umsetzung klären)

Einzeln mit dem Benutzer klären; jeden Entscheid in [decisions.md](decisions.md) eintragen und hier nachführen. Aufgeführt ist, was beim Lesen von Plan und Beispielen aufgefallen ist.

1. **Grundsatz: konstruierte Anlässe?** **Entschieden 04.11.2026:** Variante a, erfundene Texte beginnen mit `x-` (siehe decisions.md). Frage: Konstruierte Anlässe in Kauf nehmen (z. B. Bauarbeiten für den Zielwechsel, erfundene Hinweistexte) oder nur einbauen, was ohne erfundenen Kontext zu Beispiel 13 passt? Hintergrund: Die Bausteine stammen von anderen Strecken; ein Teil braucht einen Anlass, den Beispiel 13 nicht hergibt. Das Projekt verbietet erfundene NeTEx-Daten, die wie echte Auskunft wirken. Antworten: (a) konstruieren, Texte klar als Testtext kennzeichnen; (b) nur Passendes einbauen, Rest weglassen; (c) Mischform je Baustein.
1b. **Entschieden 04.11.2026:** Variante a (siehe decisions.md). **Kennzeichnung nicht-textlicher und gemischter Angaben.** Frage: Wie werden konstruierte Werte gekennzeichnet, die keinen Text haben (Zeiten, `RequestStop` true, Codes), und reale Namen in erfundener Verwendung (z. B. realer Bahnhof als neues Ziel)? Hintergrund: Vor einen Wahrheitswert oder eine Uhrzeit lässt sich kein `x-` setzen, ohne die Datei ungültig zu machen. Antworten: (a) XML-Kommentar direkt davor, beginnend mit `x-` (z. B. `<!-- x- konstruiert: Bedarfshalt -->`); (b) zusätzlich `x-` auch vor realen Namen in erfundener Verwendung; (c) nur Kommentar, reale Namen unverändert.
2. **Zielwechsel (10) ohne Anlass.** **Entschieden 04.11.2026:** Variante b, weglassen (siehe decisions.md). Frage: Wie ist der Zielwechsel auf Bern - Spiez zu begründen? Hintergrund: In Beispiel 10 endet die Fahrt nach Bauarbeiten bei Wolhusen; in Beispiel 13 fehlt ein solcher Anlass. Antworten: (a) Anlass konstruieren (Bauarbeiten, Testtext); (b) weglassen; (c) Zielwechsel ohne Notiz, nur als Anzeigewechsel.
3. **Entschieden 04.11.2026:** Variante a, weglassen; Muster in Beispiel 13 bereits vorhanden (siehe decisions.md). **Zugnummernwechsel (11) braucht eine Folgefahrt.** Frage: Wie ist er unterzubringen? Hintergrund: Er verlangt zwei `ServiceJourney` am selben Zug; SJ2 (Spiez - Zweisimmen) hat nur 2 Halte, SJ1 und SJ3 sind schon durch die Flügelung verknüpft. Antworten: (a) zusätzliche Folgefahrt ergänzen; (b) an SJ3 (Spiez - Frutigen - Brig) teilen; (c) weglassen.
4. **Formation (20).** Frage: Aufnehmen und anpassen oder weglassen? Hintergrund: Sie gehört zu Interlaken - Spiez und ist im Guide nur Entwurf (README); Linie, Halte und Fahrzeuge müssten auf Bern - Spiez angepasst werden. Antworten: (a) aufnehmen und anpassen; (b) weglassen; (c) später in eigener Datei.
5. **Anschluss (17).** Frage: Streichen? Hintergrund: Beispiel 13 enthält bereits 2 `ServiceJourneyInterchange` (SJ1-SJ2, SJ1-SJ3); 17 bringt nichts Neues. Antworten: (a) streichen; (b) nur prüfen, ob in 13 Felder fehlen, und diese ergänzen.
6. **Angebote auf RE beschränken?** Frage: Bistro/Gruppenreservation (08/15) nur auf RE-Fahrten (SJ1, SJ3), nicht auf R (SJ2)? Hintergrund: Bistro bei einem Regio ist fachlich fraglich; Beispiel 08 ist ein IC, 13 sind R/RE. Antworten: (a) nur SJ1/SJ3; (b) auch SJ2; (c) Angebote nur mit passenden Angaben aus den Beispielen (z. B. nur `wheelchairspace`).
7. **Bedarfshalt.** Frage: `RequestStop` true setzen oder weglassen? Hintergrund: In keinem Guide-Beispiel ist `RequestStop` true belegt (nur false); der Wert wäre konstruiert. Antworten: (a) setzen, im Guide-Template prüfen und kennzeichnen; (b) weglassen.
8. **Fahrt 4 (Bus aus 03).** Frage: Aufnehmen? Hintergrund: Es braucht eigene Linie, Halte und `SiteFrame`-Einträge; grosser Zusatz (Linie 803 Nyon liegt ausserdem weit von Bern - Spiez). Antworten: (a) aufnehmen; (b) weglassen; (c) als eigene kleine Datei.
9. **Fahrt 5 (Taktfahrt, `TemplateServiceJourney` aus 12).** Frage: Aufnehmen? Hintergrund: Nur sinnvoll, wenn die Fahrtansicht `TemplateServiceJourney` anzeigt (laut [open-points.md](open-points.md) ist der Takt zurückgestellt); vor dem Entscheid prüfen. Antworten: (a) aufnehmen, falls angezeigt; (b) weglassen.
10. **Dateiname.** Vorschlag `ch20_enriched_bern_spiez.xml`; bei Änderung an Punkt 11 anpassen. Antworten: Vorschlag bestätigen oder anderer Name.
11. **Alternative Basis.** Frage: Falls viele Bausteine nicht passen: anderes Beispiel als Basis (z. B. 08) oder mehrere kleine Dateien statt einer? Hintergrund: 08 hat bereits Angebote, `JourneyPart` und Hinweise, aber nur eine Fahrt; eine Datei bündelt alles, mehrere Dateien bleiben je fachlich stimmig. Antworten: (a) bei 13 bleiben; (b) 08 als Basis; (c) mehrere kleine Dateien, je Thema eine.
12. **Lizenz/Veröffentlichung.** Frage: Wie klären, und wie bis dahin verfahren? Hintergrund: Das Guide-Repo hat keine Lizenzdatei (Stand `b7ac158`); die Datei ist abgeleitet. Sie wird bis zur Klärung nicht gepusht. Antworten: (a) Anfrage an info.fachbus@sbb.ch; (b) Datei nur lokal behalten (in `.gitignore`, nicht versioniert); (c) versionieren, aber nicht pushen.
13. **Zuggattung.** Frage: Wie umgehen mit IC (08) gegenüber R/RE (13)? Hintergrund: Angebote wie Bistro sind bei IC üblich, bei RE zu klären; hängt mit Punkt 6 zusammen. Antworten: (a) Angebote an RE belassen; (b) Gattung der Fahrt ändern (verändert Beispiel 13).
14. **Hinweistexte (`Notice`) und `TypeOfNotice`.** Frage: Welche Texte und Typen? Hintergrund: Texte aus 02/03/15 gehören zu anderen Strecken; `TypeOfNotice`-Verweise müssen in `ResourceFrame` vorhanden sein. Antworten: (a) Texte wörtlich aus den Beispielen; (b) neutrale Testtexte; (c) nur Hinweise ohne Streckenbezug (z. B. Gruppenreservation).
15. **Verkehrstage.** Frage: `DayType` (03, 15) und `AvailabilityCondition` (13, 08) mischen oder bei `AvailabilityCondition` bleiben? Hintergrund: Beispiel 13 nutzt nur `AvailabilityCondition` mit `ValidDayBits`; die Weihnachts-`DayType` stammt aus anderen Beispielen. Antworten: (a) nur `AvailabilityCondition` mit Ausnahmetagen; (b) beide Konzepte zeigen.
16. **Anzeige in der Fahrtansicht.** Frage: Auch Bausteine aufnehmen, die die Fahrtansicht noch nicht darstellt? Hintergrund: Zieländerung, Formation, Takt u. a. sind in der Fahrtansicht zurückgestellt (Phase 3, Punkt 17 in [open-points.md](open-points.md)); sie hätten nur Wert für Validierung und generischen Explorer, nicht für die Fahrtansicht. Antworten: (a) nur, was die Fahrtansicht zeigt; (b) alles, als Testmaterial für Validierung und Explorer.

## Risiken und Hinweise

- ID-Konsistenz über Frames: jede neue ID eindeutig, jede Referenz mit passendem `version`, `ResourceFrame`-Objekte (`ValueSet`, `TypeOfNotice`) vor Verwendung definiert.
- Flügelzug (SJ1 mit SJ2/SJ3) nicht stören: `JourneyPart` nur mit gültigem `JourneyPatternRef`, Von-/Bis-Halt innerhalb der Fahrt.
- Keine Lieferdaten aus `../netex-files/` verwenden, keine Namen und Zeiten erfinden, die wie echte Auskunft wirken.
- Lizenz des Guide-Repos ungeklärt (keine Lizenzdatei, Stand `b7ac158`): nicht pushen, bevor geklärt (Vorgabe in `CLAUDE.md`: nichts hochladen ohne Auftrag).
- Aufwand ca. ½–1 Tag. Umsetzung an einen Sonnet-Subagenten delegierbar, Prüfung (Schritte 3 und 4) durch den Hauptagenten.

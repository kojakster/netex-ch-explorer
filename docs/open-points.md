# Offene Punkte

Werden mit dem Benutzer **einzeln** geklärt: genau ein Punkt pro Nachricht. Erledigte Punkte stehen in [decisions.md](decisions.md).

## Offen während der Umsetzung (Benutzer fragen)

1. *(Erledigt für die Kernregeln: Entscheide zu den Fragen 1–6 in [decisions.md](decisions.md) „Kernregeln Phase 4: Entscheide zu den unklaren Punkten". Offen bleibt nur: unklare Grau-Einordnungen, falls bei der Umsetzung welche auftauchen.)*
2. **Glossar Englisch/Deutsch:** Benutzer reicht nach; dann vorläufige Fachbegriffe in `de-CH.json`/`en.json` abgleichen.
3. *(Erledigt: Entscheid (3) in [decisions.md](decisions.md) „Entscheide nach Review Phase 2“, Regel Z4 in [mapping.md](mapping.md).)*
4. *(Erledigt in Phase 4: Dateien mit `DOCTYPE` weist der Einleser vor lxml ab, `parse_safely` ein zweites Mal; Tests `test_xxe_and_doctype_are_rejected_without_leaking`.)*
5. *(Erledigt: Entscheid (1) „Zieltypen aus der XSD“ in [decisions.md](decisions.md).)*
6. *(Erledigt: Entscheid (2) „Abweichende Version“ in [decisions.md](decisions.md).)*
7. **Öffnen grosser Dateien (Phase 2, Code-Review).** Die Auflösung stellt je Referenz mehrere Abfragen an den Index, und `object_detail`/`reference_view` fragen je Verweis einzeln ab (Ziel, Besitzer, Frame); alle Referenzen liegen bis zum Ende im Speicher; für die kleinen Guide-Dateien unkritisch, für grosse Lieferungen ungeeignet. Wird mit Variante B des Index (Entscheid „Index: alle Elemente im Arbeitsspeicher“) angepasst. Gilt auch für die Fahrtansicht (Phase 3): je Halt mehrere Einzelabfragen (Haltestellenzuordnung, Verweise, Stammdaten); bei den kleinen Dateien unkritisch.

18. **Phase 4: „11 Beispiele“ im Entscheid „Prüfergebnisse Guide-Beispiele“.** Die Messung mit `general_rules.sch` ergibt 121 `order`-Verstösse (Summe stimmt, Beispiel 22: 66) in **9** Beispielen (02, 03, 08, 12, 14, 19, 20, 21, 22), nicht in 11. Empfehlung: Zahl im Entscheid auf 9 berichtigen (kein Einfluss auf die Umsetzung).
19. **Phase 4: Dateien mit Version „mehrdeutig“ oder „unbekannt“ lassen sich nicht prüfen.** Eine eigene 2.0-Datei ohne genügend Hinweise (z. B. nur `version="2.1"` ohne Struktur) wird nicht gegen 2.0 geprüft (Entscheid „Eigene Dateien prüfen“: keine irreführende Prüfung). Empfehlung: ein Knopf „trotzdem als CH 2.0 prüfen“, der die Prüfung auf ausdrücklichen Wunsch erzwingt und das im Ergebnis vermerkt (kleiner Aufwand: ein Parameter im Endpunkt).
20. **Phase 4: Welches Guide-Kapitel verlinkt wird.** `A5_annex_index.md` nennt mehrere Kapitel je Element (z. B. `ServiceJourney`: 02_files, 03_xml_modelling, … 08_timetable). Umgesetzt: das erste. Für `ServiceJourney` ist das `02_files`, nicht das Kapitel der Fahrplanregeln (`08_timetable`). Empfehlung: je Regel ein festes Kapitel in der Regelliste (Kernregeln: `08_timetable`), für Schematron/XSD das erste Kapitel des Index.
21. **Phase 4: Fixtures ohne Produktkategorie.** Die `ch20_*`-Fixtures ausser `ch20_three_stops.xml` haben keine `TypeOfProductCategoryRef` und verletzen deshalb CH-SJ-07, wenn man sie prüft. Empfehlung: so lassen (jede Fixture hat ihren Zweck) oder alle ergänzen.

## Zurückgestellt

- Grosse Lieferungen (1.10-Lieferung `../netex-files/`, 12 GB): Import aus Ordner, Index auf Festplatte, Hintergrundprozess, ZIP-Grenzwerte, Lesesperre, Ausschnitte im LLM-Kontext (siehe decisions.md „Zurückgestellt …“).
- Webversion: Veröffentlichung (Zielgruppe, Ort), Lizenz der Guide-Dateien (info.fachbus@sbb.ch) und der NeTEx-CEN-XSD.
- Windows-Test von Hand, sobald ein Windows-PC verfügbar ist.
- Übrige ~330 Schweizer Profilregeln über das Build-Werkzeug des Guides.
- Auswahl mehrerer Guide-Stände in der Oberfläche; Einstellungsseite für Farben; Zellfarben der Mappingtabelle.
- Automatische Prüfung der Betriebstage von Kurswagen und Elternfahrt (Phase 3, Punkt 14; siehe decisions.md „Offene Punkte 12–17 aus Phase 3“).
- Fahrtansicht für Zieländerung (`DestinationDisplay`) als Nächstes; Takt, Formation, Flügelung, Durchbindung, Bedarfsverkehr, Elternfahrt der Kurswagen später (Phase 3, Punkt 17).

## Archiv: Findings zum ursprünglichen Plan

Alle eingearbeitet in [UMSETZUNGSPLAN.md](../UMSETZUNGSPLAN.md) (siehe [plan-abgleich.md](plan-abgleich.md)), ausser 8 und 9 (zurückgestellt mit grossen Lieferungen). **Finding 13 war falsch:** Die verschachtelten `<Text>`-Elemente in Beispiel 05/16 sind in NeTEx 2.x gültig (XSD-Prüfung am 31.10.2026: alle Beispiele gültig). Finding 14 ist geklärt: Die Daten von Beispiel 01 ergeben 10:54 (10:35 + `RunTime` 10 Min + `WaitTime` 3 Min + `RunTime` 6 Min); der Kommentar in der Datei nennt 10:53. Das Tool zeigt 10:54 mit Rechenkette; Widerspruch in `docs/assumptions.md` festhalten.

1. Abschnitt 4/Phase 3: Der Guide (2.0-Entwurf) passt nicht zur Lieferung 2027 (1.10). Entschieden ist: zuerst 2.0. Die „Realitätsprüfung mit der 2027-Lieferung“ (Abschnitte 4, 10, 11) gilt damit nur für den generischen Explorer; die Fahrtansicht wird mit den Guide-Beispielen abgenommen.
2. *(Darstellung geklärt, siehe decisions.md „Zeiten in der Fahrtansicht“; in Plan einarbeiten.)* Abschnitte 6/11: Haltefolge und Zeiten sind je Version anders modelliert. In 2.0: `ServiceJourneyPattern` + `TimeDemandType`, Zeiten berechnet. In 1.10: `calls/Call`. `TimetabledPassingTime` kommt in keiner der beiden Quellen vor (in 2.0 als deprecated markiert).
3. Verkehrstage: In 1.10 über `AvailabilityCondition`/`ValidDayBits` statt `DayType`; für 2.0 noch zu prüfen.
4. Angebote: In 1.10 steckt die Referenz in `Extensions`, der Referenz-Index muss `Extensions` also einschliessen. `FareClasses` ist nur teilweise vorhanden. Für 2.0 sind `JourneyPart` und Facilities auf Teilstrecken zu berücksichtigen (Beispiel 08).
5. Frames: `ServiceCalendarFrame` und `CompositeFrame` in die Farbliste aufnehmen. Ein Frame ist im Persistenzschema als Paar (Datei, Frame-ID) zu identifizieren.
6. Referenzauflösung: In 1.10 macht `version="any"` die Auflösung über die Version wirkungslos. Entscheidend ist der erwartete Typ (in 2.0 teilen sich `Quay` und `ScheduledStopPoint` eine ID). Am Ref-Element sind `version` und `versionRef` beide zu lesen.
7. Objekttypen, die im Plan fehlen: `TemplateServiceJourney`, `HeadwayJourneyGroup`, `TrainNumber`, `Notice`, `DestinationDisplay`, `TypeOfProductCategory`; für 2.0 zusätzlich `TimeDemandType`, `TimingLink`, `JourneyPart`, Kurswagen/Formation.
8. Abschnitt 9: ZIP-Grenzwerte realistisch wählen (Verhältnis ≥ 100:1, entpackt ≥ 20 GB), sonst wird die echte Lieferung abgelehnt.
9. README-Dateien der Lieferungen als Suchvorfilter nutzen: `Workflow/README.csv` in 1.10; laut 2.0-Guide liefert SKI ebenfalls eine README. Im Plan nicht erwähnt.
10. Abschnitt 6 „XML-Positionen“: Mit pyexpat sind exakte Byte-Offsets möglich (siehe Vorschläge in decisions.md).
11. Abschnitt 14: Arbeitsregel „keine Lieferdaten in den LLM-Kontext“ ergänzen; die europäischen Profile aus dem Text streichen bzw. unter die Nichtziele verschieben.
12. Abschnitt 4: Als Quellen die Guide-Dateien (Branch `next`, fester Commit) statt nur der Guide-Webseite nennen; die Datensätze 2026/2027 als 1.10-Quellen einordnen.
13. *(Geklärt: nicht melden, anzeigen und validieren; siehe decisions.md „Fehler in Guide-Dateien“ und „Validierung mit Erklärung“.)* Guide-Beispiele vermutlich fehlerhaft (Stand `b7ac158`): verschachtelte Elemente auf einer Zeile, `05_NeTEx_CH_DRT_Line_Dependent_On_Passengers_At_Start.xml:399` (`<Text>` innerhalb von `<Text>`) und `16_NeTEx_CH_SITE_OFFER_Connections.xml:64` (`<Text>` innerhalb von `<Name>`). Mit der XSD-Prüfung bestätigen. Der Explorer muss solche Fehler als Diagnose zeigen und darf sie nicht stillschweigend korrigieren. Ggf. an den Guide melden.
14. Beispiel 01 (Spiez – Interlaken Ost): Der Kommentar in der Datei nennt Ankunft Interlaken Ost 10:53; aus `DepartureTime` 10:35 + `RunTime` 10 Min + `WaitTime` 3 Min + `RunTime` 6 Min ergibt sich 10:54. Bei der Umsetzung anhand der vollständigen Datei prüfen (evtl. weitere Summanden oder Fehler im Kommentar/Beispiel). **Erledigt in Phase 3:** keine weiteren Summanden; Fehler im Kommentar, siehe [assumptions.md](assumptions.md).

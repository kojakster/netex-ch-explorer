# Offene Punkte

Werden mit dem Benutzer **einzeln** geklärt: genau ein Punkt pro Nachricht. Erledigte Punkte stehen in [decisions.md](decisions.md).

## Offen während der Umsetzung (Benutzer fragen)

1. **Unklare Kernregeln** und **unklare Grau-Einordnungen**, falls bei der Umsetzung welche auftauchen.
2. **Glossar Englisch/Deutsch:** Benutzer reicht nach; dann vorläufige Fachbegriffe in `de-CH.json`/`en.json` abgleichen.
3. *(Erledigt: Entscheid (3) in [decisions.md](decisions.md) „Entscheide nach Review Phase 2“, Regel Z4 in [mapping.md](mapping.md).)*
4. **Phase 4: Dateien mit `DOCTYPE` vor lxml abweisen.** lxml stürzt bei der Schema-Prüfung von `fixtures/security_xxe.xml` mit „Internal error“ ab (geprüft 31.10.2026). Die Regel steht bereits in den Qualitätsregeln; der Testfall ist vorhanden.
5. *(Erledigt: Entscheid (1) „Zieltypen aus der XSD“ in [decisions.md](decisions.md).)*
6. *(Erledigt: Entscheid (2) „Abweichende Version“ in [decisions.md](decisions.md).)*
7. **Öffnen grosser Dateien (Phase 2, Code-Review).** Die Auflösung stellt je Referenz mehrere Abfragen an den Index, und `object_detail`/`reference_view` fragen je Verweis einzeln ab (Ziel, Besitzer, Frame); alle Referenzen liegen bis zum Ende im Speicher; für die kleinen Guide-Dateien unkritisch, für grosse Lieferungen ungeeignet. Wird mit Variante B des Index (Entscheid „Index: alle Elemente im Arbeitsspeicher“) angepasst. Gilt auch für die Fahrtansicht (Phase 3): je Halt mehrere Einzelabfragen (Haltestellenzuordnung, Verweise, Stammdaten); bei den kleinen Dateien unkritisch.
12. **Phase 3, Angebote einer Teilstrecke: „überschreiben“ oder „ergänzen“?** `uc05_journey_parts.md` Z. 104 sagt, das `ServiceFacilitySet` der `JourneyPart` „overrides“ das der Fahrt; Beispiel 08 meint ergänzend (Fahrt: 1. Klasse, WLAN; Teilstrecken: Bistro). Das Tool zeigt beide getrennt und rechnet keine gültige Menge. *Empfehlung:* so lassen (ergänzend lesen), Widerspruch beim Guide-Team klären lassen; erst danach je Halt eine Gesamtmenge zeigen.
13. **Phase 3, Hinweiszuweisungen ohne Ziel (Beispiel 08, `na-1`, `na-2`).** Auf Frame-Ebene nur mit `NoticeRef`, ohne Fahrt, Fahrtmuster oder Objekt. Das Tool zeigt sie keiner Fahrt zu und meldet ihre Anzahl als ℹ Hinweis. Alternative: auf alle Fahrten des Frames anwenden (geraten). *Empfehlung:* nicht anzeigen, beim Guide-Team nachfragen, wie solche Zuweisungen gemeint sind.
14. **Phase 3, Betriebstage der Kurswagen-Teilstrecken (Beispiel 21) nicht automatisch geprüft.** Eine Prüfung „die Elternfahrt verkehrt an den verschobenen Tagen des Kurswagens“ bräuchte die Zeiten der Elternfahrt am Anfangshalt der Teilstrecke (Fahrtmuster der Elternfahrt, Tagesverschiebung, `ValidDayBits` beider Fahrten): rund einen halben bis einen Tag Aufwand. Im Beispiel 21 haben alle vier Fahrten dieselbe `AvailabilityCondition` mit 365 gesetzten Bits, die Prüfung ergäbe nichts. *Empfehlung:* zurückstellen, bis Daten mit unterschiedlichen Betriebstagen vorliegen.
15. **Phase 3, Annahmen bestätigen** ([assumptions.md](assumptions.md), Tabelle „Annahmen des Tools“): (a) Spalte `Abk` des Blatts `VMArt->NeTEx` entspricht dem `ShortName` der Produktkategorie; (d) `StartTime` einer `JourneyPart` ist die Abfahrt am Anfangshalt, `EndTime` die Ankunft am Endhalt (Beispiel 08 bestätigt es); (e) Zeitumstellung am letzten Sonntag im März und Oktober; (f) Hinweiszuweisungen auf Frame-Ebene mit `JourneyPatternRef` gelten für alle Fahrten des Musters. *Empfehlung:* alle bestätigen.
16. **Phase 3, Befunde der Fahrtansicht und Beispielstatus.** Die Diagnosen der Art `projection` entstehen beim Abruf einer Fahrt, stehen nur dort und zählen weder in die Diagnosenliste des Datensatzes noch in den Beispielstatus (14 von 22 Beispielen hätten sonst eine Warnung wegen `ValidDayBits`). *Empfehlung:* so lassen; mit Phase 4 (Kernregeln) neu entscheiden, welche Befunde als Profilregel gelten.
17. **Phase 3, nicht dargestellte Inhalte.** Zieländerung (`DestinationDisplay` am Halt, 13 Halte in den Beispielen), Takt (`frequencyGroups`), Formation, Flügelung, Durchbindung, Bedarfsverkehr und die Elternfahrt der Kurswagen erscheinen nur im Objekt-Explorer (Plan Abschnitt 6: „nach Bedarf“). *Empfehlung:* als Nächstes die Zieländerung (kleiner Aufwand, steht für Reisende im Fahrplan), den Rest später.

## Zurückgestellt

- Grosse Lieferungen (1.10-Lieferung `../netex-files/`, 12 GB): Import aus Ordner, Index auf Festplatte, Hintergrundprozess, ZIP-Grenzwerte, Lesesperre, Ausschnitte im LLM-Kontext (siehe decisions.md „Zurückgestellt …“).
- Webversion: Veröffentlichung (Zielgruppe, Ort), Lizenz der Guide-Dateien (info.fachbus@sbb.ch) und der NeTEx-CEN-XSD.
- Windows-Test von Hand, sobald ein Windows-PC verfügbar ist.
- Übrige ~330 Schweizer Profilregeln über das Build-Werkzeug des Guides.
- Auswahl mehrerer Guide-Stände in der Oberfläche; Einstellungsseite für Farben; Zellfarben der Mappingtabelle.

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

# Offene Punkte

Werden mit dem Benutzer **einzeln** geklärt: genau ein Punkt pro Nachricht. Erledigte Punkte wandern nach [decisions.md](decisions.md).

## Offene Fragen

1. ~~Guide-Dateien kopieren oder von GitHub holen?~~ → geklärt, siehe decisions.md.
2. ~~Rolle der 1.10-Lieferung~~ → geklärt: zurückgestellt, siehe decisions.md.
3. *(Zurückgestellt mit der 1.10-Lieferung)* Sind kleine XML-Einzelausschnitte der Lieferung im LLM-Kontext erlaubt oder nur zusammengefasste Auswertungen?
4. *(Zurückgestellt mit der 1.10-Lieferung)* Soll die Lesesperre für `../netex-files/` eingerichtet werden?
5. Vorschläge von Claude bestätigen (je einzeln): ~~5a pyexpat~~ → geklärt; ~~5b XPath-Speicherung~~ → geklärt; ~~5c XML-Anzeige~~ → geklärt: CodeMirror 6.
5a. ~~Webversion?~~ → geklärt: lokal + statische Webversion (Pyodide), siehe decisions.md.
5f. *(Zurückgestellt)* Webversion: Zielgruppe (öffentlich/intern) und Ort der Veröffentlichung. Bis dahin überall lauffähig bauen, siehe decisions.md.
5g. ~~Guide-Dateien in der Webversion~~ → geklärt: mitausliefern, siehe decisions.md.
5g'. *(Vor öffentlicher Veröffentlichung)* Lizenz für die Weiterverteilung der Guide-Dateien (info.fachbus@sbb.ch) und der NeTEx-CEN-XSD klären.
5h. ~~Speicher im Browser~~ → geklärt: nur Arbeitsspeicher, siehe decisions.md. *(5d ZIP-Entpacken und 5e Import-Reihenfolge: zurückgestellt mit grossen Lieferungen.)*
6. ~~Ordnerstruktur~~ → geklärt, siehe decisions.md. Umzug von `CLAUDE.md`, `docs/` und Plan nach `netex-explorer/` erledigt (30.10.2026).
7. Git-Repository für `netex-explorer/` anlegen (`git init`), inkl. `.gitignore`. Noch nicht gemacht; erst auf Wunsch des Benutzers.

## Findings zum Implementierungsplan

1. Abschnitt 4/Phase 3: Der Guide (2.0-Entwurf) passt nicht zur Lieferung 2027 (1.10). Entschieden ist: zuerst 2.0. Die „Realitätsprüfung mit der 2027-Lieferung“ (Abschnitte 4, 10, 11) gilt damit nur für den generischen Explorer; die Fahrtansicht wird mit den Guide-Beispielen abgenommen.
2. Abschnitte 6/11: Haltefolge und Zeiten sind je Version anders modelliert. In 2.0: `ServiceJourneyPattern` + `TimeDemandType`, Zeiten berechnet. In 1.10: `calls/Call`. `TimetabledPassingTime` kommt in keiner der beiden Quellen vor (in 2.0 als deprecated markiert).
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
13. Guide-Beispiele vermutlich fehlerhaft (Stand `b7ac158`): verschachtelte Elemente auf einer Zeile, `05_NeTEx_CH_DRT_Line_Dependent_On_Passengers_At_Start.xml:399` (`<Text>` innerhalb von `<Text>`) und `16_NeTEx_CH_SITE_OFFER_Connections.xml:64` (`<Text>` innerhalb von `<Name>`). Mit der XSD-Prüfung bestätigen. Der Explorer muss solche Fehler als Diagnose zeigen und darf sie nicht stillschweigend korrigieren. Ggf. an den Guide melden.

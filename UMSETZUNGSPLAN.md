# NeTEx CH Explorer – Umsetzungsplan, erste Ausbaustufe

**Status:** Entwurf zur Prüfung durch den Benutzer. Ersetzt nach Freigabe [NETEX_EXPLORER_IMPLEMENTATION_PLAN.md](NETEX_EXPLORER_IMPLEMENTATION_PLAN.md).
**Stand:** 30.10.2026
**Massgebend für Details:** [docs/decisions.md](docs/decisions.md). Bei Abweichungen gilt `decisions.md`; der Widerspruch wird dem Benutzer vorgelegt.
**Abgleich mit dem ursprünglichen Plan:** [docs/plan-abgleich.md](docs/plan-abgleich.md)

## 1. Ziel

Ein lokales Werkzeug, mit dem man Schweizer NeTEx-Dateien **versteht**. Man wählt ein Beispiel aus dem CH-NeTEx-Guide oder öffnet eine eigene Datei. Dann sieht man eine einzelne Fahrt wie einen Fahrplan, kann jede Angabe bis zur exakten Stelle im XML zurückverfolgen, Referenzen vor- und rückwärts navigieren und Fehler mit Stelle und Guide-Verweis erkennen.

Grundsätze (aus [CLAUDE.md](CLAUDE.md)): klein und wartbar vor ausgefeilten Funktionen; Aufwand offenlegen; Unklarheiten dem Benutzer vorlegen.

## 2. Umfang

### Erste Ausbaustufe (dieser Plan)

1. Lokale Anwendung: Start per Skript, Bedienung im Browser.
2. `update-guide`: Guide-Stand laden, Bericht über Änderungen, Tests, Lock aktualisieren.
3. Alle Dateien in `src/examples/` des Guide-Stands einzeln ladbar, auch fehlerhafte.
4. Fahrtansicht für eine `ServiceJourney`: Halte, Ankunft/Abfahrt (auch berechnete Zeiten), Mitternacht, Betriebstage, Angebote.
5. Herkunft jeder angezeigten Angabe bis zur exakten Stelle im XML.
6. Objekt-Explorer mit Referenzen vor- und rückwärts und Frame-Zugehörigkeit.
7. Stammdaten: Code und Bedeutung aus der Mappingtabelle.
8. Eigene Dateien öffnen: XML, mehrere XML, ZIP.
9. Validierung Grundstufe: XSD und Guide-Schematron mit Stelle und Link zum Guide-Kapitel.
10. Oberfläche in Deutsch und Englisch, alle Texte in Sprachdateien.

### Später (nicht in diesem Plan, Schnittstellen nicht verbauen)

- Webversion (statisch, Pyodide). Der Kern wird dafür von Anfang an ohne Server-Abhängigkeiten gebaut.
- Validierung: deutsche Erklärungen und Korrekturvorschläge.
- Auswahl mehrerer Guide-Stände in der Oberfläche (Lock-Datei ist dafür schon eine Liste).
- Grosse Lieferungen (z. B. 1.10-Lieferung, 12 GB), Adapter für CH 1.10.
- Weitere Oberflächensprachen.

### Nichtziele

- Kein Fahrplanauskunftssystem, keine Verbindungssuche, keine Gesamtnetz-Darstellung.
- Keine Korrektur oder Veränderung von Dateien; das Tool liest nur.
- Keine Profile anderer Länder.
- Keine Aussage „gültig“ nur weil eine Datei lesbar ist; Prüfungen gegen den Entwurf heissen „geprüft gegen Entwurf <Commit>“.

## 3. Verbindliche Regeln für Daten und Anzeige

| Regel | Umsetzung |
|---|---|
| **Herkunft** | Jede angezeigte Angabe hat eine Herkunft: Objekt, Frame, Datei, Zeile/Spalte, Pfad. Ein Klick markiert die exakte Stelle im XML. Abgeleitete Angaben zeigen die Kette ihrer Quellen. |
| **Nichts erfinden** | Fehlendes oder nicht Auflösbares wird als solches angezeigt („nicht in dieser Datei aufgelöst“, „nicht berechenbar“), nie durch Standardwerte ersetzt. |
| **XML bleibt XML** | Werte, Codes und Texte aus den Dateien werden unverändert angezeigt, nie übersetzt. Mehrsprachige Texte: alle Fassungen mit Sprachkennzeichen. Der NeTEx-Elementname wird immer mit angezeigt. |
| **Codes und Stammdaten** | Immer den gesendeten Code zeigen. Bedeutung nur aus der Datei selbst oder aus der Mappingtabelle (mit Blatt, Zeile, Guide-Stand), sonst „keine Erläuterung in den Stammdaten“. |
| **Frames** | Frame-Typ und Frame-ID aus der tatsächlichen XML-Struktur; Frame ist eindeutig als (Datei, Frame-ID). |
| **Robustheit** | Fehlerhafte Dateien werden so weit wie möglich geladen; Fehler erscheinen als Diagnose, nie als Absturz. |
| **Diagnosen getrennt** | Arten: Datei/ZIP, XML-Syntax, XSD, Profilregel (Schematron), Referenz (`unresolved`, `ambiguous`), Projektion (z. B. „nicht berechenbar“, Widerspruch). Nie vermischen. |

## 4. Datenquellen

### Guide-Stand

- Lock-Datei `netexRealisationGuideSwitzerland.lock.json` im Projekt (Liste benannter Stände; zunächst ein Eintrag „2.0 Entwicklung“, Ref `next`, Commit, XSD-Commit, Status „in Entwicklung“).
- Dateien liegen in `../netexRealisationGuideSwitzerland/<commit>/` (Pfad konfigurierbar): Guide-Repo als Commit-Archiv von GitHub, XSD separat von NeTEx-CEN auf dem im Guide gepinnten Commit.
- Daraus genutzt: `src/examples/*.xml` + `README.md` (Titel), `src/templates/` (später für Vorschläge), `src/schematron_rules/general_rules.sch`, `xsd/`, `src/A5_annex_index.md` (Element → Kapitel), `src/media/Mappingtabellen_NeTEx_v2.0.xlsx`.

### `update-guide` (ein Befehl, `scripts/update-guide.sh` / `.ps1`)

1. Neuesten Commit von `next` und den zugehörigen XSD-Commit ermitteln.
2. Beides nach `../netexRealisationGuideSwitzerland/<commit>/` laden (nur Python-Standardbibliothek, kein Git nötig).
3. Mappingtabelle auslesen → `mapping.json` beim Stand (Spalten über ihre Namen; fehlt eine, Abbruch mit klarer Meldung; Zellfarben werden ignoriert).
4. Bericht: neue, geänderte, entfernte Dateien (Beispiele, Templates, Schematron, XSD, Mappingtabelle).
5. Tests gegen den neuen Stand ausführen; nur bei Erfolg den Lock auf den neuen Commit setzen.

### Eigene Dateien

XML, mehrere XML oder ZIP aus dem lokalen Dateisystem bzw. per Dateiauswahl im Browser an das lokale Backend. Zuerst Versionserkennung, dann Prüfung (siehe Abschnitt 8).

## 5. Architektur

```text
netex-ch-explorer/
├── app/
│   ├── core/       Python-Paket ohne Server-Abhängigkeiten (läuft später auch unter Pyodide)
│   │   ├── reader/        Einlesen mit pyexpat: Objekte, Referenzen, Frames, Positionen
│   │   ├── index/         SQLite (im Arbeitsspeicher): Objekte, Referenzen, Pfadformen, Diagnosen
│   │   ├── guide/         Guide-Stand, Beispiel-Liste, Mappingtabelle, Kapitel-Index
│   │   ├── profiles/      Versionserkennung; Adapter „generisch“ und „CH 2.0“
│   │   ├── projection/    Fahrtansicht CH 2.0 mit Herkunft je Feld
│   │   └── validation/    XSD und Schematron (lxml)
│   ├── server/     FastAPI, nur dünne Schicht über core; bindet an 127.0.0.1
│   └── frontend/   React + TypeScript + Vite, CodeMirror 6, Sprachdateien
├── scripts/        update-guide, start (.sh/.ps1)
├── fixtures/       eigene synthetische Testdateien (keine Guide-Kopien)
└── docs/
```

| Baustein | Festlegung |
|---|---|
| Python | 3.12+ (lokal 3.13); Abhängigkeiten mit Lockfile. |
| Einlesen | **pyexpat**: pro Element Byte-Offset, Zeile, Spalte; eigene Verschachtelungs- und Namespace-Behandlung; Kommentare werden für die Versionserkennung gelesen. Keine externen Entitäten, kein Netzwerkzugriff. |
| Index | SQLite im Arbeitsspeicher je geöffnetem Datensatz. Pfadformen einmal in eigener Tabelle; Objekte speichern Datei, Offset, Zeile, Spalte, Frame. Vollständiger Pfad mit Positionsnummern wird beim Anzeigen berechnet. |
| Referenzen | Aus allen `…Ref`-Elementen (auch in `Extensions`). Auflösung über (ID, erwarteter Typ aus Ref-Name bzw. `nameOfRefClass`); `version` und `versionRef` beide lesen. Status: `resolved`, `unresolved`, `ambiguous`. |
| Prüfung | lxml nur für XSD und Schematron. |
| Oberfläche | React + TypeScript + Vite; CodeMirror 6 (nur lesen, exakte Bereichsmarkierung). |
| Texte | Keine Texte im Code. Sprachdateien `de-CH.json`, `en.json`; Kern liefert Schlüssel + Parameter; kleine eigene Übersetzungsfunktion. Deutsche Fachbegriffe vorläufig bis zum Glossar. |
| Plattformen | macOS; Windows plattformneutral programmiert, aber als „nicht getestet“ gekennzeichnet. |

### Schnittstelle (lokal, JSON)

| Aufruf | Zweck |
|---|---|
| `GET /api/guide` | Aktiver Guide-Stand, Liste der Beispiele mit Titeln |
| `POST /api/datasets` | Datensatz öffnen: Beispiel-Name oder eigene Datei(en)/ZIP |
| `GET /api/datasets/{id}` | Dateien, Versionserkennung, Anzahl Diagnosen |
| `GET /api/datasets/{id}/objects?type=&q=&limit=&offset=` | Objektsuche, paginiert |
| `GET /api/objects/{id}` | Eigenschaften mit Herkunft, Frame, Referenzen ein-/ausgehend |
| `GET /api/objects/{id}/xml` | XML-Ausschnitt mit Positionen für die Markierung |
| `GET /api/journeys/{id}` | Fahrtansicht mit Herkunft je Feld |
| `GET /api/datasets/{id}/diagnostics?category=&severity=` | Diagnosen |
| `POST /api/datasets/{id}/validate` | XSD-/Schematron-Prüfung starten |

Einheitliches Fehlerformat; Texte nur als Schlüssel. Vertrag in `docs/api.md`.

## 6. Fachliche Abbildung CH 2.0 (Fahrtansicht)

Jede Regel wird in `docs/mapping.md` mit Guide-Datei, Abschnitt und Commit belegt. Grundlage: [docs/research/guide-2.0.md](docs/research/guide-2.0.md).

| Inhalt | Abbildung im Guide | Anzeige |
|---|---|---|
| Haltefolge | `ServiceJourney` → `ServiceJourneyPatternRef` → `StopPointInJourneyPattern` (Reihenfolge) → `ScheduledStopPoint` → `PassengerStopAssignment` → `StopPlace`/`Quay` | Halte in Reihenfolge, Name aus der Datei, Kante falls zugeordnet |
| Zeiten | `DepartureTime` + `TimeDemandTypeRef` → `JourneyRunTime`/`JourneyWaitTime` je `TimingLink` | Ankunft/Abfahrt wie ein Fahrplan, Markierung „berechnet“, Rechenkette mit Quellen; fehlt ein Summand: „nicht berechenbar“ |
| Mitternacht | `DepartureDayOffset` (fehlend = 0, als Standardwert gekennzeichnet); Tageswechsel während der Fahrt nur rechnerisch; `JourneyPart` mit `Start-/EndTimeDayOffset` | „+1“/„−1“ je Zeit, ausdrücklich oder berechnet; Widersprüche als Diagnose; Hinweis in Nächten der Zeitumstellung |
| Betriebstage | `AvailabilityConditionRef` → `AvailabilityCondition` (`FromDate`, `ToDate`, `ValidDayBits`); `DayType` nur Feiertage | Gültigkeitszeitraum und Anzahl Tage; Liste der Tage aufklappbar. Keine Pauschalaussagen wie „Mo–Fr“ |
| Linie, Verkehrsmittel | `LineRef` im `ServiceJourneyPattern`; `TransportMode`/Submode; `TypeOfProductCategoryRef` | Text aus der Datei, Codes mit Stammdaten |
| Angebote | Facilities/`ServiceFacilitySet`, auch nur auf Teilstrecken bzw. an einzelnen Tagen (`JourneyPart`) | Code + Bedeutung aus Mappingtabelle; Gültigkeit (Teilstrecke/Tage) mit Herkunft |
| Hinweise | `NoticeAssignment` → `Notice/Text` | Text unverändert, alle Sprachen |

Nicht eigens dargestellte Inhalte (Kurswagen, Formation, Flügelung, Durchbindung, DRT) sind über den Objekt-Explorer vollständig einsehbar; Erweiterung der Fahrtansicht nach Bedarf.

## 7. Oberfläche

- **Links:** aktiver Guide-Stand (mit „in Entwicklung“), Auswahl der Beispiele bzw. „Datei öffnen“, Versionserkennung, Suche, Objekttypen, Diagnosen.
- **Mitte:** umschaltbar „Fahrt“ / „Objekt“. Fahrt: Kopf mit Linie, Verkehrsmittel, Betriebstagen; Tabelle Halt – Ankunft – Abfahrt – Angebote. Objekt: Eigenschaften und Referenzen ein-/ausgehend als Liste (siehe offene Frage 1).
- **Rechts:** Herkunft der gewählten Angabe (Kette), Frame mit Farbe, Textlabel und ID, XML-Ausschnitt mit Markierung.
- Klick auf eine Angabe synchronisiert Auswahl, Herkunft und XML-Markierung. Zurück-Navigation (Verlauf) bleibt erhalten.
- Frame-Farben zentral in `frontend/src/theme/frames.ts` für `CompositeFrame`, `ResourceFrame`, `SiteFrame`, `ServiceFrame`, `ServiceCalendarFrame`, `TimetableFrame` und unbekannte Frames; Farbe nie als einzige Information.
- Sprachumschaltung Deutsch/Englisch.

## 8. Versionserkennung und Validierung (Grundstufe)

- **Versionserkennung** mit Begründung: Namespace, `version`-Attribut, `schemaLocation`, Kommentare, Dateiname, Struktur. Ergebnis `detected`, `ambiguous` oder `unknown`; das Wurzelattribut allein entscheidet nie (die Guide-Beispiele tragen teils `1.09`).
- **Passt die Datei nicht zum Guide-Stand** (z. B. 1.10-Lieferung): Ergebnis anzeigen, keine 2.0-Prüfung starten, generischer Explorer bleibt nutzbar.
- **XSD-Prüfung** (lxml) gegen die XSD des Guide-Stands; Fehler mit Datei, Zeile, Spalte, Markierung im XML.
- **Schematron:** `general_rules.sch` des Guides (siehe offene Frage 3).
- **Link zum Guide-Kapitel** über `A5_annex_index.md`, auf GitHub im exakt verwendeten Commit.
- Ergebnis heisst „geprüft gegen Entwurf <Commit>“, nie „gültig“.
- Bekannte erste Testfälle: Beispiel 05 Zeile 399, Beispiel 16 Zeile 64, `TypeOfName` `offical`.

## 9. Sicherheit

- pyexpat ohne externe Entitäten und ohne Netzwerkzugriff; lxml mit `resolve_entities=False`, `no_network=True`.
- ZIP: Zip-Slip-Schutz, keine Symlinks, Grenzwerte für Gesamtgrösse, Einzeldatei und Kompressionsrate (konfigurierbar, für die erste Ausbaustufe klein gewählt).
- Server nur auf `127.0.0.1`, CORS nur für das lokale Frontend, keine freien Dateipfade über die API, keine Telemetrie, keine Cloud-Dienste.
- Hochgeladene Dateien nur in einem definierten Arbeitsverzeichnis; Aufräumen beim Schliessen des Datensatzes.

## 10. Phasen und Abnahme

Nach jeder Phase: Tests ausführen, Ergebnis in `docs/test-report.md`, Commit. Fehler vor der nächsten Phase beheben.

| Phase | Inhalt | Abnahme |
|---|---|---|
| **0 Grundgerüst** | Projektstruktur, Abhängigkeiten mit Lockfiles, `update-guide` inkl. Mappingtabelle und Bericht, Start-Skripte, leere Oberfläche mit Sprachdateien | `update-guide` lädt `b7ac158` + XSD `73b337e`, erzeugt `mapping.json` und Bericht; App startet lokal |
| **1 Einlesen und Objekt-Explorer** | pyexpat-Reader, Index, Frames, Pfade, Syntax-Diagnosen, Objektsuche, Objektdetail, XML-Ansicht mit Markierung, Beispielauswahl | **Alle Guide-Beispiele** laden ohne Absturz; ID-Suche zeigt Objekt mit Frame, Datei, Zeile/Spalte; Klick markiert exakt die Stelle |
| **2 Referenzen und Herkunft** | Referenzen inkl. `Extensions`, Auflösung über ID + Typ, Rückwärtsreferenzen, Herkunftsanzeige, Frame-Farben | Navigation vor/zurück; `Quay` und `ScheduledStopPoint` mit gleicher ID werden korrekt unterschieden; nicht auflösbare Referenzen als Diagnose |
| **3 Fahrtansicht CH 2.0** | Haltefolge, berechnete Zeiten mit Rechenkette, Mitternacht, Betriebstage, Linie/Verkehrsmittel, Angebote inkl. `JourneyPart`, Hinweise, Stammdaten | Beispiel 01 zeigt die Halte in richtiger Reihenfolge und nachvollziehbar berechnete Zeiten mit Rechenkette (Abweichung zum Dateikommentar 10:53/10:54 geklärt und in `docs/assumptions.md` festgehalten); Beispiel 15 (`DepartureDayOffset` 1) und 21 (Kurswagen über Mitternacht) korrekt; Beispiel 08 zeigt Angebote auf Teilstrecken |
| **4 Eigene Dateien und Validierung** | Öffnen von XML/mehreren XML/ZIP, Versionserkennung, XSD + Schematron, Guide-Kapitel-Links | Eigene 2.0-Datei wird geprüft; 1.10-Datei wird erkannt und nicht irreführend geprüft; Fehler in Beispiel 05/16 erscheinen mit Stelle und Link |
| **5 Übergabe** | README, Start/Stopp, E2E-Test, Testbericht, bekannte Grenzen, Sprachdatei-Prüfung | Neue Person startet die App, lädt Beispiel 01, klickt einen Halt an und landet an der richtigen XML-Stelle, ohne Code zu ändern |

## 11. Tests

- **Unit:** Namespaces, Positionen (Byte/Zeile/Spalte), Frame-Zuordnung, Pfadberechnung, Referenzauflösung (ID + Typ, doppelte IDs), Zeitberechnung inkl. Mitternacht und fehlender Summanden, `ValidDayBits`, Versionserkennung, Mappingtabelle (fehlende Spalte → Abbruch), Übersetzungsschlüssel vollständig.
- **Alle Guide-Beispiele:** parametrisierter Test lädt jedes Beispiel des aktiven Guide-Stands; keine Abstürze, Diagnosen erlaubt.
- **Synthetische Fixtures** (eigene, klein): Fahrt mit drei Halten, Fahrt über Mitternacht, fehlender Summand, nicht auflösbare Referenz, doppelte ID, defektes XML, ZIP mit mehreren Dateien, 1.10-artige Datei.
- **Sicherheit:** XXE, Zip-Slip, ZIP-Grenzwerte, unzulässiger Pfad.
- **E2E (Playwright, ein Pfad):** Beispiel 01 laden → Fahrt öffnen → Halt anklicken → richtige XML-Stelle und Frame.
- **Keine festen Texte im Frontend-Code:** einfacher Prüftest.

## 12. Dokumentation

`README.md` (Start, Bedienung, bekannte Grenzen, Windows ungetestet), `docs/mapping.md` (jede fachliche Regel mit Guide-Beleg), `docs/api.md`, `docs/assumptions.md` (Annahmen, Widersprüche im Guide), `docs/test-report.md`. Entscheidungen weiterhin in `docs/decisions.md`.

## 13. Offene Fragen an den Benutzer (beim Schreiben entstanden)

1. **Referenzgraph:** Der ursprüngliche Plan sieht einen grafischen Referenzgraphen (Cytoscape.js) vor. Für das Verstehen reicht in der ersten Ausbaustufe vermutlich eine **Liste** der ein- und ausgehenden Referenzen mit Navigation; der Graph wäre eine zusätzliche Bibliothek und Ansicht. Graph jetzt, später oder gar nicht?
2. **Vereinfachung Index und Import:** Die Guide-Beispiele sind 4–56 KB gross. Vorschlag: Index nur im Arbeitsspeicher und **kein Hintergrund-Importjob** in der ersten Ausbaustufe (Laden dauert Millisekunden). Beides kommt erst mit grossen Lieferungen. Einverstanden?
3. **Schematron:** Im Guide-Repo liegt nur `general_rules.sch` (4 Regeln). Die übrigen Regeln erzeugt das Build-Werkzeug des Guides aus den Templates. Erste Ausbaustufe nur mit `general_rules.sch`, und die erzeugten Regeln später (nach Prüfung des Build-Werkzeugs)?
4. **Widerspruch in `decisions.md`:** „Plattformen“ verlangt Tests auf macOS und Windows, „Windows“ sagt „derzeit nicht testbar“. Vorschlag: „Plattformen“ an „Windows“ anpassen.

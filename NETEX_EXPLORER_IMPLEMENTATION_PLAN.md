# NeTEx Explorer CH — Implementierungsauftrag für VS Code / Coding-Agent

**Status:** Umsetzungsauftrag für einen lokal lauffähigen Prototyp  
**Stand:** 30.10.2026  
**Sprache der Anwendung:** Deutsch (de-CH), NeTEx-Bezeichner unverändert  
**Ziel:** NeTEx-Lieferungen gezielt untersuchen und fachliche Angaben lückenlos auf ihre XML-Quelle zurückführen.

## 1. Arbeitsauftrag an den Coding-Agenten

Erstelle im aktuellen Workspace eine **lokal ausführbare Webapplikation** namens **NeTEx Explorer CH**. Implementiere zunächst einen vertikalen, tatsächlich nutzbaren Prototyp: NeTEx-Dateien importieren, Objekte indexieren, eine `ServiceJourney` suchen, ihren Fahrtverlauf darstellen, referenzierte Objekte navigieren und jede visualisierte Eigenschaft zum Original-XML zurückverfolgen.

**Nicht** nur Mockups, statische Beispieldaten oder eine Architektur-Skizze abliefern. Implementiere lauffähigen Code, automatisierte Tests, ein Startskript und eine README. Die NeTEx-Daten dürfen niemals stillschweigend erfunden, ergänzt oder aus vermeintlichem Fachwissen abgeleitet werden. Nicht auflösbare Daten explizit kennzeichnen.

Arbeite in den Phasen aus Abschnitt 10. Nach jeder Phase Tests ausführen; vor der nächsten Phase Fehler korrigieren. Falls eine fachliche Zuordnung aufgrund der Quellenlage unklar ist, die Unsicherheit in der Anwendung sichtbar machen und in `docs/assumptions.md` dokumentieren. Nicht ungeprüft von einem europäischen NeTEx-Profil auf das Schweizer Profil schliessen.

## 2. Zielbild und Nutzerablauf

1. Benutzer öffnet `http://localhost:5173` (oder die in der README dokumentierte lokale URL).
2. Benutzer lädt eine XML-Datei, mehrere XML-Dateien oder eine ZIP-Lieferung hoch; alternativ kann er einen lokalen Ordner per dokumentiertem Backend-Import verwenden.
3. Import zeigt Dateien, Status, Warnungen und erkannte Profilinformationen an.
4. Benutzer sucht `ServiceJourney` nach ID, Linien-/Fahrtnummer oder zugehöriger Haltestelle, soweit die Daten dafür auflösbar sind.
5. Benutzer wählt eine Fahrt; zentral erscheint **nur diese Fahrt**, nicht der gesamte Fahrplan.
6. Die Fahrtansicht zeigt, soweit aus den Daten eindeutig ableitbar: Linien-/Fahrtbezeichnung, Transportmodus, geordnete Halte, Ankunft/Abfahrt, Betriebs-/Verkehrstage und Angebote wie 1./2. Klasse.
7. Klick auf einen Halt, eine Zeit oder ein Angebot öffnet die zugehörigen NeTEx-Objekte und ihren Referenzpfad; in der XML-Ansicht wird die exakte Quellstelle hervorgehoben.
8. Benutzer navigiert Referenzen vorwärts und rückwärts und erkennt, in welchem **Frame** das Objekt tatsächlich enthalten ist.
9. Parser-, Schema-, Profil- und Referenzprobleme sind mit Ursache und möglichst Datei/Zeile/Objekt sichtbar; ansonsten funktionierende Teilbereiche bleiben bedienbar.

Zweite Perspektive neben der fachlichen Fahrtansicht: **Technischer Objekt-Explorer** mit Objekten, Eigenschaften, Referenzen, XML und Frame-Zuordnung. Suche nach Haltestellen kann im MVP zunächst auf die Objektansicht führen; eine vollständige Haltestellen-Abfahrtstafel ist nicht erforderlich.

## 3. Scope / Nichtziele

### MVP (verbindlich)

- Lokaler Import: einzelne `.xml`, mehrere `.xml`, `.zip` mit XML-Dateien.
- Streaming-Import ohne vollständiges Laden grosser Lieferungen in den Arbeitsspeicher.
- Index der identifizierten NeTEx-Objekte und Referenzen mit Dateiname, XML-Pfad und Zeileninformation, wo verfügbar.
- Suche und Detailansicht für `ServiceJourney`, `Line`, `JourneyPattern`, `ScheduledStopPoint`, `StopPlace`, `Quay` und andere tatsächlich vorkommende Objekte als generische Fallback-Ansicht.
- Darstellung einer einzelnen ausgewählten Fahrt: geordnete Halte und Zeiten **nur bei nachgewiesener Auflösung**; keine erfundenen Werte.
- Interaktive Referenznavigation: von Objekt zu referenziertem Objekt sowie Rückwärtsreferenzen.
- Darstellung von Frame-Typ und konkreter Frame-ID auf Basis **tatsächlicher XML-Elternstruktur**; konsistente Farben je Frame-Typ.
- Quellnachweis je visualisiertem Feld: Datei, XML-Element/-Attribut, XPath oder äquivalenter Pfad, Zeile falls bestimmbar, Referenzkette.
- Unterschiedliche Probleme differenziert ausweisen; unvollständiger Import darf nutzbare Daten nicht vollständig sperren.
- Profil-Erkennung als **best effort**; fehlende/mehrdeutige Erkennung deutlich anzeigen.
- README, Beispieldaten (synthetisch, klein), Tests und Reproduktionsanleitung.

### Nach MVP (Schnittstellen vorbereiten, nicht als fertig deklarieren)

- Versionierte Profiladapter für weitere Schweizer Profilversionen.
- XSD-/Schematron-Prüfung mit passenden versionierten Regeln, falls öffentlich zugänglich und eindeutig zugeordnet.
- Grössere aggregierte Haltestellenansicht und leistungsfähige Filter.
- Kartenansicht, Kalenderaufbereitung aller Verkehrstage, Export/Screenshots, Deep Links.
- Hintergrundjobs und Abbruch-/Wiederaufnahme-Funktion für mehrstündige Imports.

### Explizite Nichtziele

- Kein vollständiger Journey Planner, keine Suche nach Umsteigeverbindungen.
- Keine Darstellung des gesamten Schweizer Netzes auf einmal.
- Kein produktiver Datenimport für INFO+ und keine Korrektur von Lieferdateien.
- Keine Behauptung, dass eine XML-Datei aufgrund erfolgreichem Parsing fachlich valide ist.

## 4. Fachliche Quellen und Verifikation

**Massgebend für die Schweiz:**

- NeTEx Realisation Guide Switzerland: https://opentdatach.github.io/netexRealisationGuideSwitzerland/main/index.html
- Guide-Repository: https://github.com/openTdataCH/netexRealisationGuideSwitzerland
- Reale Testlieferung 2027: https://data.opentransportdata.swiss/dataset/timetablenetex_2027
- Optionaler Versionsvergleich: https://data.opentransportdata.swiss/de/dataset/timetablenetex_2026

**Vor der Implementierung fachlicher Mappings:**

1. Relevante Abschnitte des Schweizer Guides und die Beispiel-XML des Repositorys prüfen.
2. XML-Struktur von mindestens einer realen, geeigneten Datei aus der 2027-Lieferung inspizieren; umfangreiche Datensätze nicht unkontrolliert herunterladen.
3. Für jede implementierte Ableitung dokumentieren, welche Objekttypen, `...Ref`-Kanten und XML-Elemente genutzt werden.
4. Nur tatsächlich verifizierte Beziehungen als allgemeine Regel kodieren. Beispiel: `ServiceJourney` und `JourneyPattern` oder `TimetabledPassingTime` sind Suchbegriffe, keine automatisch vollständige/überall gültige Kette.
5. Verweise auf die XSDs/Profilregeln mit Herkunft und Version dokumentieren; ohne passende Regeln keine erfolgreiche Schema- oder Profilkonformität behaupten.

**Wichtige Differenzierung:** XML-Namespace, NeTEx/XSD-Version, Schweizer Profilversion und Guide-Dokumentationsstand sind unterschiedliche Angaben. Sie dürfen nicht zu einer einzigen „Version“ zusammengefasst werden. Lieferungsdateinamen können Hinweise geben, sind aber kein alleiniger Nachweis.

## 5. Architektur und Technologien

**Frontend:** React + TypeScript + Vite, Cytoscape.js für Referenzgraph, Monaco Editor für XML. **Backend:** Python 3.12+, FastAPI, `lxml` (sicher konfiguriert), SQLite mit geeigneten Indizes und optional FTS. **Tests:** pytest (Backend), Vitest (Frontend), Playwright für mindestens einen End-to-End-Pfad.

Die Architektur ist bewusst lokal und ohne Cloud-Abhängigkeit. Browser übermittelt Dateien nur an das auf `127.0.0.1` gebundene Backend. Kein automatischer Upload an Drittanbieter, keine Telemetrie. CORS nur für das lokale Frontend.

### Komponenten

- **ImportService:** Dateianalyse, sichere ZIP-Verarbeitung, XML-Parsing, Fortschritt, Teilfehler.
- **ObjectIndex:** identifizierte XML-Objekte mit Typ/ID/Version/Datei/Position, Frame-Zugehörigkeit.
- **ReferenceIndex:** Referenzkanten aus expliziten XML-Referenzen; Zielauflösung, Rückwärtsnavigation; mehrdeutige IDs kennzeichnen.
- **ProfileDetector:** Beweismittel sammeln (Namespaces, Root/Schema-Attribute, Metadaten, Dateinamen); `detected`, `ambiguous`, `unknown` mit Begründung. Profiladapter nicht mit Dokumentationsversion verwechseln.
- **JourneyProjection:** aus verifizierten Objekt- und Referenzketten die Ansicht einer `ServiceJourney` erzeugen; jedes angezeigte Feld hat `provenance`.
- **ValidationService:** getrennte Diagnosen für ZIP/Import, XML-Syntax, XSD (nur bei passendem Schema), Profile (nur bei bekannten Regeln), nicht auflösbare oder mehrdeutige Referenzen.
- **API:** Paginierte Suche und kleine Detailantworten, keine vollständigen Datensatz-Downloads an das Frontend.
- **UI:** Importstatus, Suche, Fahrtansicht, Objektgraph, Properties/XML/Diagnosen.

### Persistenz (Vorschlag)

`datasets(id, name, imported_at, status, profile_status, profile_evidence_json)`  
`files(id, dataset_id, path, size_bytes, parse_status, diagnostics_count)`  
`objects(id, dataset_id, file_id, netex_id, element_name, netex_version, frame_type, frame_id, xpath, line, display_name)`  
`refs(id, dataset_id, source_object_id, ref_element_name, target_netex_id, target_object_id_nullable, resolution_status, xpath, line)`  
`diagnostics(id, dataset_id, file_id_nullable, object_id_nullable, severity, category, message, line_nullable, xpath_nullable)`.

Zielbeziehung nicht ausschliesslich anhand der ID auflösen, wenn sie mehrdeutig ist; `version`, erwarteter Objekttyp und Kontext berücksichtigen. SQLite-Index auf Dataset/Objekt-ID/Typ und Source/Target von Referenzen.

### Schnittstellenvorschlag

- `POST /api/datasets/import` — Multipart-Upload, Dataset-ID und Status liefern.
- `GET /api/datasets` — vorhandene Lieferungen.
- `GET /api/datasets/{id}/status` — Dateistatistik, Importstatus, Profilbeweismittel.
- `GET /api/datasets/{id}/objects?type=&q=&limit=&offset=` — paginierte Suche.
- `GET /api/objects/{id}` — Eigenschaften, Frame, Referenzen, Rückwärtsreferenzen.
- `GET /api/objects/{id}/xml` — XML-Ausschnitt und Quellort, serverseitig limitiert.
- `GET /api/objects/{id}/references` — paginierte Kanten samt Auflösungsstatus.
- `GET /api/journeys/{object_id}` — Fahrtprojektion mit Provenance je Feld.
- `GET /api/datasets/{id}/diagnostics?category=&severity=&limit=&offset=`.

Alle Backend-Outputs mit konsistenten Fehlerformaten, typsicheren Response-Modellen und Limits versehen. Der API-Vertrag ist innerhalb des Projekts in `docs/api.md` zu dokumentieren.

## 6. XML-Auflösung und Nachvollziehbarkeit

### Unverzichtbare fachliche Regel

**Jede angezeigte Aussage muss auf ein XML-Element, Attribut oder eine nachvollziehbare Referenzkette zurückführbar sein.** Die UI zeigt pro Information: Wert, Quellobjekt, Frame, Datei und XML-Pfad. Mehrere erforderliche Quellen werden als Kette sichtbar. Steht etwas nicht explizit in der Lieferung, aber wird über einen verifizierten Bezug abgeleitet, muss die Ableitung kenntlich sein.

Beispiele für zu untersuchende Objekte/Konzepte (nicht als unbesehen gültige Mappingdefinition verwenden):

- `ServiceJourney`: einzelne geplante Fahrt.
- `JourneyPattern` und `StopPointInJourneyPattern`: Haltefolge.
- `TimetabledPassingTime`: geplante Zeiten am Halt; korrekte Zuordnung über die referenzierten Musterpunkte.
- `ScheduledStopPoint`, `StopPlace`, `Quay`: fahrplanbezogene Punkte und physische Haltestellen-/Haltekantenbezüge; unterschiedliche Konzepte nicht vermischen.
- `Line`, `TransportMode` / weitere Typisierung: Linie und Verkehrsart.
- `DayType` und zugehörige Zuordnungen: Verkehrstage; ohne vollständige Auflösung keine Pauschalaussage wie „Mo–Fr“.
- `ServiceFacilitySet` und verknüpfte Angebotsinformationen: 1./2. Klasse und sonstige Einrichtungen **nur anzeigen, wenn die konkrete Lieferung dies belegt**.

Auch falls Informationen in einem anderen Frame definiert sind, bestimmt **die tatsächlich gefundene Containerhierarchie** die Farbe. Keine pauschale Zuordnung von Begriffen zu Frames. XML-Objekte dürfen über Frame-Grenzen referenziert werden.

### Frame-Farbkonzept

Konstante, voneinander unterscheidbare Farben für `ResourceFrame`, `SiteFrame`, `ServiceFrame`, `TimetableFrame` und weitere tatsächlich vorkommende Frame-Typen; zusätzlich Textlabel und Frame-ID (nicht nur Farbe als Information). Die konkreten Farben zentral in `frontend/src/theme/frames.ts` definieren. Widersprüche zwischen Guide, Templates und Beispielen nicht verdecken: bei abweichender XML-Platzierung **Ist-Frame anzeigen**, und wenn notwendig eine erläuternde Diagnose.

### XML-Positionen

`lxml` liefert oft Zeilennummern, jedoch nicht verlässlich Spalten. XPath muss robust gegen Namespaces sein. `lxml` ist kein garantierter Byte-Offset-Indexer: Für die XML-Ansicht Quellfile und, soweit verfügbar, Zeile plus Elementkontext benutzen; wenn exakte Hervorhebung unsicher ist, transparent auf Objekt-/Zeilenebene hervorheben statt Präzision vorzutäuschen. Bei Streaming-Parsing erforderliche Metadaten **vor dem Freigeben von XML-Teilbäumen** speichern.

## 7. UI-Entwurf

Desktop-zentrierte, responsive Dreispaltenansicht:

**Links (~25 %):** aktive Lieferung, Profilstatus, Suchfeld, Objektkategorien, Suchresultate, Import- und Diagnoseanzeige.  
**Mitte (~45 %):** umschaltbar „Fahrt“ / „Referenzgraph“; pro Halt Reihenfolge, Anzeigename, Zeit und Status; Graph nur für ausgewähltes Objekt plus begrenzte Nachbarschaft.  
**Rechts (~30 %):** Properties, Quellnachweis, Frame/Frame-ID, XML-Ausschnitt mit Highlight, ein- und ausgehende Referenzen.

Klick auf fachliche Eigenschaft synchronisiert (a) ausgewähltes Objekt, (b) Graphfokus und (c) XML-Ansicht. Nutzer kann entlang einer Referenz vorwärts und rückwärts gehen; Breadcrumb/Zurück-Navigation beibehalten. Fehler und fehlende Daten niemals mit Standardwerten ersetzen.

Visualisierungsbegrenzung: nur eine ausgewählte Fahrt bzw. ein ausgewähltes Objekt und seine begrenzten Verbindungen darstellen; Suchergebnisse paginieren; Graph-Tiefe standardmässig 1, auf Anfrage höchstens 2, jeweils Knotenlimit.

## 8. Versionierung und Validierung

**Erkennung:** Implementiere zunächst `ProfileDetector` als nachvollziehbare Heuristik. UI zeigt: NeTEx-Namespace, Schema-Hinweis (falls vorhanden), Profilangabe (falls vorhanden), Dateinamen-Hinweise, Erkennungsstatus und Vertrauen/Begründung. `unknown` und `ambiguous` sind reguläre Ergebnisse, kein Crash.

**Adapter-Schnittstelle:** `ProfileAdapter` mit Methoden für Objekterkennung, Referenzinterpretation, Journey-Projektion und optional Profilvalidierung. Ein generischer Adapter ist immer verfügbar. Einen CH-spezifischen Adapter erst dann als kompatibel markieren, wenn er an konkreten Guide-/Beispieldaten getestet wurde. Unbekannte Profile: generischer XML-/Referenz-Explorer, fachliche Darstellung nur für nachgewiesen unterstützte Ableitungen.

**Validierung:**

- Syntax: defektes XML mit Dateiname/Zeile melden.
- XSD: nur wenn exakt geeignete XSD verfügbar ist und die Verarbeitung die Validierung ausführt; sonst `not_checked`, nie „gültig“.
- Profil: nur für implementierte und belegte Regeln; sonst `not_checked`.
- Referenzen: `resolved`, `unresolved`, `ambiguous`, ggf. `external_or_unloaded` unterscheiden.
- Fehlende Datei und fehlendes Referenzziel unterscheiden, soweit möglich.

## 9. Sicherheit und Performance

- XML-Parser ohne externe Entitäten/Netzwerkzugriffe (`resolve_entities=False`, `no_network=True`); keine unkontrollierte DTD/XXE-Verarbeitung.
- ZIP-Pfade gegen Zip-Slip prüfen, Symlinks und gefährliche Einträge ausschliessen; maximale entpackte Gesamtgrösse, Einzeldateigrösse und Kompressionsrate konfigurierbar; nicht das gesamte ZIP im RAM entpacken.
- Uploads, temporäre Dateien und Datenbanken in einem definierten lokalen Arbeitsverzeichnis; Upload-/Importfehler bereinigen.
- Parsing mit `iterparse` bzw. äquivalentem Streaming, Speicher freigeben, ohne erforderliche Referenzen oder Provenance zu verlieren.
- Keine blockierende Verarbeitung der kompletten Lieferung im HTTP-Request: Importjob mit Statusabfrage (lokaler Worker reicht fürs MVP).
- Teilfehler sauber persistieren; vollständige Lieferungen werden nur soweit indexiert, wie die lokale Maschine Ressourcen erlaubt.
- Dateisystempfade serverseitig validieren; keine freien Pfadzugriffe über API.
- Sicherheit und Performance durch Tests mit grossen künstlichen Dateien und fehlerhaften ZIPs belegen.

## 10. Implementierungsphasen und Definition of Done

### Phase 0 — Projekt und Fachanalyse

**Umsetzung:** Repo-Struktur aufbauen, Guide/Beispiel-XML studieren, Version-/Frame-Konzept dokumentieren, kleine synthetische Testlieferung erstellen, reale 2027-Struktur stichprobenartig prüfen. `docs/mapping.md` mit überprüften Referenzketten anlegen. **Ergebnis:** lokal startfähiges Grundgerüst und nachvollziehbare Fachentscheidungen.

### Phase 1 — Import und generischer XML-Explorer

**Umsetzung:** XML-/ZIP-Import, sicherer Streaming-Parser, SQLite-Index, Diagnosen, Objektsuche, Objekt-/XML-Detail, Namespace-Handhabung. **Abnahme:** XML und ZIP importierbar; eine bewusst fehlerhafte XML wird isoliert mit Fehlermeldung angezeigt; andere Dateien bleiben zugänglich; ID-Suche liefert Quelle/Frame.

### Phase 2 — Referenzgraph und Quellnachweis

**Umsetzung:** Explizite XML-Referenzen aufnehmen, Rückwärtsreferenzen, generischer Graph, XML-Anzeige synchronisieren, Framefarben. **Abnahme:** Klick auf Referenz öffnet korrektes Ziel oder dokumentierte fehlende/mehrdeutige Auflösung; Quellpfad korrekt; Framefarbe entspricht der realen Hierarchie.

### Phase 3 — Einzelne Fahrt fachlich darstellen

**Umsetzung:** Schweizer Guide-basierte Projektion `ServiceJourney`, Haltefolge, Zeiten, Haltestellenbezug, soweit vorhanden Verkehrsmodus/Angebote/Verkehrstage. Fehlende Angaben erscheinen als „nicht in dieser Lieferung aufgelöst“; die Quelle jedes Felds ist anklickbar. **Abnahme:** Synthetischer Test mit mindestens drei Halten und verknüpften Dateien zeigt die richtige Reihenfolge, Zeiten und Source-Provenance; Gegenprobe mit realer Schweizer Lieferung.

### Phase 4 — Profilstatus und belastbare Qualitätsanzeige

**Umsetzung:** versionierte Adapter-Schnittstelle, Erkennung mit Beweismitteln, Diagnosefilter, optional XSD nur bei belegbarer Übereinstimmung, offene Abweichungen im UI. **Abnahme:** erkannte und unbekannte Profile sowie XML-/Referenzfehler klar unterscheidbar, keine falsche Konformitätsanzeige.

### Phase 5 — Bedienbarkeit und Übergabe

**Umsetzung:** E2E-Tests, verständliche README, lokale Start-/Stop-Kommandos, Testbericht, Performanceprobe, bekannte Einschränkungen. **Abnahme:** Neue Person kann Anwendung in VS Code starten, Testdaten importieren, eine Fahrt suchen, einen Halt anklicken und zur XML-Quelle navigieren, ohne Code zu ändern.

## 11. Tests (mindestens)

- **Unit:** Namespaces, Identifikation und Frame-Zuordnung; `id`/`version`; Referenzauflösung; ProfileDetector; JourneyProjection einschliesslich nicht auflösbarer Angaben.
- **Integration:** Mehrere XMLs in einer ZIP, dateiübergreifende Referenz, fehlende Referenz, doppelte ID, teilweise defekte Lieferung, XML ohne unterstütztes Profil.
- **Security:** XXE, Zip-Slip, ZIP-Bomben-Grenzwerte, unzulässiger Dateipfad.
- **E2E:** Import → Suche `ServiceJourney` → Fahrt mit 3 Halten → Halt anklicken → korrekte XML-Quelle und Frame-Farbe.
- **Realitätsprüfung:** Mindestens eine echte Datei der Schweizer 2027-Lieferung; Ergebnis und nicht unterstützte Teile dokumentieren. Keine synthetischen Daten als reale Fahrplandaten ausgeben.

## 12. Lieferobjekte und Ordnerstruktur

```text
netex-explorer-ch/
├── README.md
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── importer/
│   │   ├── index/
│   │   ├── profiles/
│   │   ├── projection/
│   │   ├── validation/
│   │   └── models/
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── theme/frames.ts
│   └── tests/
├── fixtures/
│   ├── README.md
│   └── synthetic/
├── docs/
│   ├── mapping.md
│   ├── api.md
│   ├── assumptions.md
│   └── test-report.md
└── scripts/
    ├── start.sh
    └── start.ps1
```

Python- und Frontend-Abhängigkeiten mit Lockfiles oder reproduzierbar dokumentierten Versionen festhalten. Die synthetischen Fixtures müssen zulässige Weitergabe erlauben. Keine grossen echten Datensätze ins Git-Repository committen.

## 13. Verbindliche Erfolgskriterien

- [ ] Lokales Starten mit dokumentierten Kommandos in VS Code möglich.
- [ ] XML und ZIP lassen sich importieren; Dateifehler isolieren.
- [ ] Eine reale oder synthetische `ServiceJourney` kann über die UI gefunden werden.
- [ ] Einzelne Fahrt mit Halten/Zeiten sichtbar, sofern die Daten das hergeben.
- [ ] Klick auf ein angezeigtes Feld zeigt nachweisbar die korrekte XML-Herkunft.
- [ ] Frame-Typ wird aus der Datei bestimmt, Frame-Farben sind konsistent.
- [ ] Referenzen navigierbar und Rückwärtsreferenzen sichtbar.
- [ ] Fehlende/mehrdeutige Referenzen werden nicht geraten.
- [ ] Profile werden nur aufgrund vorliegender Beweismittel erkannt; unbekannte Profile bleiben untersuchbar.
- [ ] Syntax-, Schema-, Profil- und Referenzprüfungen werden nicht miteinander verwechselt.
- [ ] Tests laufen und README nennt bekannte Grenzen.

## 14. Handlungsanweisung für den Coding-Agenten

**Beginne jetzt mit Phase 0 und implementiere anschliessend die Phasen 1–5 im aktuellen Workspace.** Weise vor jeder fachlichen Zuordnung auf Quellen in `docs/mapping.md` hin, verwende echte referenzierbare XML-Quellen und setze nicht unterstützte Anforderungen als explizite Einschränkung um. Führe nach jeder Phase Tests aus; halte Änderungen, Testergebnisse und verbleibende Einschränkungen in `docs/test-report.md` fest. Bei Architekturentscheidungen die einfachste zuverlässige Lösung bevorzugen. Verwende keine cloudbasierten Dienste zur Verarbeitung der importierten Fahrplandaten. Falls Laufzeit-, Download- oder Zugangsgrenzen eine Phase verhindern, liefere den funktionsfähigen Teil mit präziser Fehlerbeschreibung statt simuliertem Erfolg.

# Abgleich: ursprünglicher Plan → neuer Umsetzungsplan

Zeigt für jeden Abschnitt des ursprünglichen Plans `NETEX_EXPLORER_IMPLEMENTATION_PLAN.md` (Stand 30.10.2026; aus dem Projekt entfernt, im Git-Verlauf: `git show 62ab791:NETEX_EXPLORER_IMPLEMENTATION_PLAN.md`), wo der Inhalt im [UMSETZUNGSPLAN.md](../UMSETZUNGSPLAN.md) steht oder warum er entfällt bzw. sich ändert. Verweise auf Entscheidungen beziehen sich auf [decisions.md](decisions.md).

| Ursprünglicher Abschnitt | Im neuen Plan | Änderung / Begründung |
|---|---|---|
| **1 Arbeitsauftrag** (lauffähiger Prototyp, Tests, README; nichts erfinden; Phasen mit Tests; Unklarheiten dokumentieren) | 1 Ziel, 3 Regeln, 10 Phasen, 12 Doku | Übernommen. Neu: Unklarheiten werden dem Benutzer **vorgelegt**, nicht nur dokumentiert (CLAUDE.md, Grundsätze). „Nicht vom europäischen Profil schliessen“ entfällt: nur CH-Profile im Umfang (Entscheid „Umfang Profile“). |
| **2 Zielbild/Nutzerablauf** (Upload, Suche, nur eine Fahrt, Klick → XML, Referenzen, Frames, Diagnosen) | 1 Ziel, 2 Umfang, 6, 7 Oberfläche | Übernommen. Einstieg neu über **Beispielauswahl** aus dem Guide (Entscheid „Alle Guide-Beispiele ladbar“). **Suche vereinfacht** (Benutzer, 30.10.2026): Datei wählen, Liste der Fahrten der Datei, einfache Objektsuche nach ID/Name; keine Suche nach Linie/Zugnummer/Haltestelle. Zugnummer und Halt-Eigenschaften (Ein-/Aussteigen, Bedarfshalt) in der Fahrtansicht. Port 5173 bleibt Vite-Standard. |
| **3 Scope MVP** | 2 Umfang | Inhaltlich übernommen. **Geändert:** „Streaming ohne vollständiges Laden grosser Lieferungen“ zurückgestellt (Entscheid „Grosse Lieferungen zurückgestellt“); Architektur bleibt dafür offen. |
| **3 Nach MVP** | 2 „Später“ | Übernommen und ergänzt um Webversion, Erklärungen/Korrekturvorschläge, Auswahl Guide-Stände. Karte, Kalenderaufbereitung, Export, Deep Links: weiterhin später, nicht eigens aufgeführt. |
| **3 Nichtziele** | 2 Nichtziele | Übernommen. „Kein produktiver Import für INFO+“ ist durch „keine Veränderung von Dateien“ abgedeckt. |
| **4 Quellen** (Guide-Webseite, Repo, Testlieferung 2027, 2026) | 4 Datenquellen | **Geändert:** Grundlage sind die **Dateien des Guide-Repos** auf festem Commit, nicht die Webseite (Entscheide „Erste Zielversion“, „Guide-Dateien beziehen“). Lieferungen 2026/2027 sind NeTEx 1.10 und zurückgestellt ([research/delivery-1.10-2027.md](research/delivery-1.10-2027.md)). |
| **4 Verifikation vor Mappings** (Guide prüfen, Herkunft dokumentieren, keine ungeprüften Ketten) | 6 Fachliche Abbildung | Übernommen: jede Regel mit Beleg in `docs/mapping.md`. Fachliche Ketten sind jetzt am Guide verifiziert ([research/guide-2.0.md](research/guide-2.0.md)). |
| **4 Versionsangaben nicht vermischen** | 8 Versionserkennung | Übernommen, konkretisiert (Wurzelattribut allein entscheidet nie). |
| **5 Architektur: React/Vite** | 5 | Übernommen. |
| **5 Cytoscape.js** | 7 Oberfläche | **Entfällt** (Benutzer, 30.10.2026): keine Graph-Bibliothek; stattdessen Frame-Farben als roter Faden, Herkunftskette als farbige Kästchen, farbige Referenzliste, XML-Ansicht mit farbigen Frame-Bereichen. |
| **5 Monaco** | 5 | **Ersetzt** durch CodeMirror 6 (Entscheid „XML-Anzeige“). |
| **5 Python/FastAPI** | 5 | Übernommen; FastAPI nur dünne Schicht über einem server-unabhängigen Kern (Entscheid „Betriebsformen“). |
| **5 lxml für Parsing** | 5 | **Geändert:** pyexpat zum Einlesen, lxml nur für Prüfung (Entscheid „XML-Parser“). |
| **5 SQLite (+FTS)** | 5 | SQLite bleibt, in der ersten Ausbaustufe im Arbeitsspeicher (offene Frage 2). FTS entfällt vorerst (Beispiele klein). |
| **5 pytest/Vitest/Playwright** | 11 | Übernommen. |
| **5 Lokal, 127.0.0.1, keine Telemetrie, CORS** | 9 Sicherheit | Übernommen. |
| **5 Komponenten** (ImportService, ObjectIndex, ReferenceIndex, ProfileDetector, JourneyProjection, ValidationService, API, UI) | 5 Module `reader`, `index`, `guide`, `profiles`, `projection`, `validation`, `server`, `frontend` | Übernommen mit neuer Aufteilung; neu `guide` für Guide-Stand, Beispiele, Mappingtabelle. |
| **5 Persistenzschema** (`datasets`, `files`, `objects` mit `xpath`, `refs`, `diagnostics`) | 5 Index | **Geändert:** keine XPath-Zeichenkette pro Objekt, Pfadformen in eigener Tabelle, Positionen mit Byte/Zeile/Spalte (Entscheid „XML-Pfad im Index“); Frame als (Datei, Frame-ID). Genaues Schema entsteht in Phase 1. |
| **5 Schnittstellen** | 5 Schnittstelle | Übernommen und angepasst: neu `GET /api/guide`, `POST /api/datasets/{id}/validate`; `/references` in `/objects/{id}` enthalten. |
| **6 Herkunftsregel** | 3 Regeln | Übernommen, unverändert verbindlich. |
| **6 Beispielobjekte** (`JourneyPattern`, `TimetabledPassingTime`, `DayType`, `ServiceFacilitySet` …) | 6 Fachliche Abbildung | **Geändert gemäss Guide 2.0:** Zeiten über `TimeDemandType` (berechnet), `TimetabledPassingTime` ist im Guide veraltet; Betriebstage über `AvailabilityCondition`/`ValidDayBits`, `DayType` nur Feiertage. |
| **6 Frame-Farbkonzept** | 7 Oberfläche | Übernommen; ergänzt um `CompositeFrame`, `ServiceCalendarFrame`. |
| **6 XML-Positionen** (lxml nur Zeilen, ggf. ungenau markieren) | 5 Einlesen | **Verbessert:** exakte Positionen mit pyexpat. |
| **7 UI-Entwurf** (drei Spalten, Synchronisation, Breadcrumb, Begrenzung Graph) | 7 Oberfläche | Übernommen; Graph entfällt; ersetzt durch farbige Herkunftskette und Referenzliste. Neu: Sprachumschaltung, Beispielauswahl. |
| **8 ProfileDetector** | 8 Versionserkennung | Übernommen. |
| **8 ProfileAdapter** | 5 `profiles` | Übernommen: Adapter „generisch“ und „CH 2.0“. |
| **8 Validierung** (Syntax, XSD nur passend, Profil nur belegt, Referenzstatus) | 3 Diagnosen, 8 Validierung | Übernommen; „geprüft gegen Entwurf <Commit>“ statt „gültig“. Status `external_or_unloaded` bleibt: Haltestellen fehlen in `NETWORK_OFFER`-Dateien laut Guide (ATLAS), Ziele in nicht geöffneten Dateien. |
| **9 Sicherheit** | 9 | Übernommen; ZIP-Grenzwerte vorerst klein (grosse Lieferungen zurückgestellt). |
| **9 Performance** (iterparse, Importjob, grosse künstliche Dateien) | 2 „Später“, 13 offene Frage 2 | **Zurückgestellt** mit grossen Lieferungen. |
| **10 Phasen 0–5** | 10 Phasen 0–5 | Struktur übernommen; Inhalte und Abnahmen an Guide 2.0 und die Entscheide angepasst; neue Phase 4 „Eigene Dateien und Validierung“. |
| **11 Tests** | 11 | Übernommen; neu: Test über alle Guide-Beispiele, Mitternacht, Übersetzungsschlüssel. „Realitätsprüfung mit 2027-Lieferung“ entfällt (1.10, zurückgestellt). |
| **12 Ordnerstruktur** `netex-explorer-ch/` | 5 Architektur | **Ersetzt** durch `netex-ch-explorer/` mit `app/`, Guide ausserhalb (Entscheid „Ordnerstruktur“). |
| **12 Lockfiles, keine grossen Daten im Repo** | 5, CLAUDE.md | Übernommen. |
| **13 Erfolgskriterien** | 10 Abnahmen | In die Abnahmen der Phasen überführt. |
| **14 Handlungsanweisung** | 10 Phasen, CLAUDE.md | Übernommen, inkl. „funktionierenden Teil mit genauer Lückenbeschreibung liefern statt vorgetäuschtem Erfolg“ (Abschnitt 10). Arbeitsregeln (keine Lieferdaten ins LLM, einzelne Fragen, Aufwand offenlegen) stehen in CLAUDE.md. |

## Bewusst nicht übernommen

- Realitätsprüfung mit der 2027-Lieferung (NeTEx 1.10, zurückgestellt).
- Performanceprobe mit grossen Dateien (zurückgestellt).
- Volltextsuche (FTS): bei kleinen Dateien nicht nötig.
- Diagnose „Objekt steht in anderem Frame als vom Guide vorgesehen“: Ist-Frame wird angezeigt; Soll-Prüfung wäre Zusatzaufwand mit fraglichem Nutzen, evtl. später in der Validierung.
- Suche nach Linie, Zugnummer oder Haltestelle (Benutzer: Fahrplandarstellung wichtiger als Suche).

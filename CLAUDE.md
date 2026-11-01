# NeTEx CH Explorer

Lokales Werkzeug, um Schweizer NeTEx-Dateien visuell und selbsterklärend zu verstehen: Fahrt als Fahrplan, Herkunft jeder Angabe bis zur exakten Stelle im XML, klare Frame-Farben, alle Objekte und Verweise, Fehler mit Guide-Verweis.

Sprache der Anwendung und der Dokumentation: Deutsch (de-CH); NeTEx-Bezeichner bleiben unverändert.

## Wo was steht

- [UMSETZUNGSPLAN.md](UMSETZUNGSPLAN.md): gültiger Plan für die erste Ausbaustufe. Abschnitt 13 beschreibt die Arbeitsweise. Umsetzung nur auf Aufforderung des Benutzers; erledigte Phasen stehen in `docs/test-report.md`.
- [docs/decisions.md](docs/decisions.md): alle Entscheidungen. **Geht dem Plan vor.** Vor jeder Umsetzungs- oder Architekturarbeit lesen.
- [docs/open-points.md](docs/open-points.md): offene und zurückgestellte Punkte.
- [docs/research/guide-2.0.md](docs/research/guide-2.0.md): CH-Profil 2.0: Artefakte, Lieferstruktur, Datenmodell, Mitternacht, Codes, Prüfergebnisse.
- [docs/research/delivery-1.10-2027.md](docs/research/delivery-1.10-2027.md): Lieferung 2027 (NeTEx 1.10) in `../netex-files/`, zurückgestellt.
- [docs/engineering-guidelines.md](docs/engineering-guidelines.md): verbindliche Qualitätsregeln (Sicherheit, Wartbarkeit, Erweiterbarkeit, Tests, Selbstkontrolle).
- [README.md](README.md): Einrichtung (Guide klonen, Workspace, Start).
- [CHECKLIST.md](CHECKLIST.md): Findings des Benutzers aus dem Testen (nicht versioniert, in `.gitignore`). Nur auf ausdrückliche Anweisung bearbeiten; Regeln in `../CLAUDE.md`.

## Umfang in Kürze

- Nur Schweizer NeTEx-Definitionen; CH-Versionen über versionierte Adapter plus generischen Explorer.
- Zielversion: **neueste Version des CH-Profils 2.0 (Entwurf, NeTEx 2.1)** aus dem Guide-Klon (Branch `next`).
- Lokal auf macOS und Windows. Eine Webversion (Pyodide) kommt später; der Kern ist deshalb ein reines Python-Paket ohne Server-Abhängigkeiten.

## Verzeichnisse

```text
NeTEx-Viewer/                          Sammelordner (nicht versioniert)
├── netexRealisationGuideSwitzerland/  fremder Inhalt: Git-Klon des Guides (Branch next) + XSD-Submodul
├── netex-files/                       Lieferdaten
└── netex-ch-explorer/                 dieses Projekt (eigenes Git-Repository)
```

- `../netexRealisationGuideSwitzerland/` ist ein Git-Klon des Benutzers; nur per Git aktualisieren (`git pull`, `git submodule update --init --depth 1`), Dateien nie von Hand ändern. Zuletzt getesteter Stand: `guide-tested.json`.
- Eigener Code liegt nur in `netex-ch-explorer/`. Guide-Dateien nie hierher kopieren, auch nicht nach `fixtures/`; `fixtures/` enthält nur selbst erstellte Testdaten.
- Pfade zu `netexRealisationGuideSwitzerland` und `netex-files` nur über `config/settings.json` (Standard `../netexRealisationGuideSwitzerland`, `../netex-files`), nie fest im Code.
- Der Adapter „CH 2.0“ ist eigener Code. Er belegt jede fachliche Regel in `docs/mapping.md` mit Guide-Datei und Commit.

## Grundsätze

- **Klein und wartbar vor ausgefeilten Funktionen.** Die einfachste Lösung, die die Anforderung erfüllt, hat Vorrang.
- **Aufwand offenlegen:** Bedeutet eine Anforderung viel Code oder eine komplexe Lösung, sage ich das *vor* der Umsetzung, mit grober Einschätzung und einfacherer Alternative. Das gilt besonders, wenn der Nutzen fraglich ist. Der Benutzer entscheidet.
- **Unklarheiten und Widersprüche** (im Plan, in Entscheidungen, im Guide oder in den Daten) nicht selbst auflösen, sondern dem Benutzer vorlegen und gemeinsam klären. Danach in `docs/decisions.md` festhalten.

## Codequalität (verbindlich)

- **Keine Sicherheitslücken, wartbar, erweiterbar, Best Practice, keine Abkürzungen.** Details: [docs/engineering-guidelines.md](docs/engineering-guidelines.md). Ich halte mich selbst konsequent daran und kontrolliere es selbst.
- **`scripts/check.py` muss vor jedem Commit grün sein** (Stil, `mypy --strict`, Tests mit ≥ 90 % Abdeckung im Kern, Frontend-Prüfung, Sicherheitslücken in Abhängigkeiten). Der Git-Hook erzwingt das; **`--no-verify` ist verboten.**
- **Vor jedem Phasenabschluss** Code-Review und Sicherheits-Review; Funde beheben; Nachweis in `docs/test-report.md`.
- Ausnahmen von Prüfregeln nur mit Begründung im Code und in `docs/decisions.md`.

## Arbeitsregeln

- **Keine Lieferdaten in den LLM-Kontext.** Grosse Lieferungen (z. B. `../netex-files/`, 12 GB) nur lokal per Skript auswerten; in den Kontext kommen nur zusammengefasste Ausgaben (Zählungen, Strukturen, Messwerte). Nie ganze Dateien lesen; einzelne kleine Ausschnitte nur gezielt und sparsam. Die Beispieldateien des Guides sind öffentliche Dokumentation und davon nicht betroffen.
- Entwicklung und automatisierte Tests auf den Guide-Beispielen und kleinen synthetischen Fixtures.
- Python, das Lieferdaten oder Guide-Dateien für Analysen liest, mit `python3 -I` ausführen. Code aus dem Guide-Repo (z. B. `tools/`) nicht ungeprüft ausführen.
- NeTEx-Daten nie erfinden oder ergänzen; nicht Auflösbares explizit kennzeichnen.
- **Echte Bezeichnungen verwenden:** Fremde Quellen heissen im Projekt so wie im Original, z. B. Ordner `netexRealisationGuideSwitzerland` nach dem GitHub-Repo `openTdataCH/netexRealisationGuideSwitzerland`. Keine eigenen Kurznamen erfinden.
- Vorgaben aus Plan und Entscheidungen dürfen hinterfragt werden; Abweichungen gemeinsam mit dem Benutzer festlegen.
- **Fragen einzeln klären:** genau eine Frage bzw. ein Punkt pro Nachricht. Erst wenn er geklärt und in `docs/decisions.md` eingetragen ist, folgt der nächste.
- **Hilfeseite immer nachführen:** Jede Änderung an Funktionen, Frame-Farben, Grau-Liste, Schweregraden oder Prüfungen (neu, geändert, entfernt, „nicht durchgeführt“) führt die Hilfeseite und die Sprachdateien (de/en) **im selben Commit** nach. Ein Test stellt sicher, dass nichts ohne Hilfetext bleibt; vor jedem Commit prüfen. Gleiches gilt für das README bei Änderungen an Einrichtung oder Start.
- Nichts auf GitHub oder andere Server hochladen, ausser der Benutzer verlangt es ausdrücklich.
- Neue Entscheidungen in `docs/decisions.md` eintragen, neue Rechercheergebnisse unter `docs/research/`. Diese Datei bleibt kurz und enthält nur dauerhaft gültige Regeln.

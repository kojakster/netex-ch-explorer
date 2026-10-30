# NeTEx Explorer CH

Lokale Webapplikation zum Untersuchen Schweizer NeTEx-Lieferungen. Ziel: eine `ServiceJourney` suchen, ihren Fahrtverlauf darstellen, Referenzen navigieren und jede angezeigte Angabe auf ihre XML-Quelle zurückführen (Datei, Byte-Offset/Zeile, Frame).

Sprache der Anwendung und der Dokumentation: Deutsch (de-CH); NeTEx-Bezeichner bleiben unverändert.

## Wo was steht

- [NETEX_EXPLORER_IMPLEMENTATION_PLAN.md](NETEX_EXPLORER_IMPLEMENTATION_PLAN.md): ursprünglicher Auftrag, **noch nicht überarbeitet**.
- [docs/decisions.md](docs/decisions.md): festgelegte Entscheidungen und unbestätigte Vorschläge. **Geht dem Plan vor.** Vor jeder Umsetzungs- oder Architekturarbeit lesen.
- [docs/open-points.md](docs/open-points.md): offene Fragen und Findings zum Plan.
- [docs/research/guide-2.0.md](docs/research/guide-2.0.md): CH-Profil 2.0 (Entwurf): Artefakte, Lieferstruktur, Datenmodell.
- [docs/research/delivery-1.10-2027.md](docs/research/delivery-1.10-2027.md): lokale Lieferung 2027 (NeTEx 1.10) in `../netex-files/`.

## Umfang in Kürze

- Nur Schweizer NeTEx-Definitionen; mehrere CH-Versionen über versionierte Adapter plus generischen Explorer.
- Betriebsformen: lokal **und** statische Webversion, bei der die Verarbeitung im Browser über Pyodide läuft. Der Kern ist deshalb ein reines Python-Paket ohne Server-Abhängigkeiten.
- Erste Zielversion: **neueste Version des CH-Profils 2.0 (Entwurf, NeTEx 2.1)**. Abgebildet mit den Dateien des Guide-Repos (Branch `next`, fester Commit), die ein Skript von GitHub lädt.

## Verzeichnisse

```text
NeTEx-Viewer/                          Sammelordner (nicht versioniert)
├── netexRealisationGuideSwitzerland/  fremder Inhalt: Guide-Dateien + XSD je Commit
├── netex-files/                       Lieferdaten
└── netex-ch-explorer/                 dieses Projekt (eigenes Git-Repository)
```

- In `../netexRealisationGuideSwitzerland/` nie von Hand etwas ändern; nur `scripts/update-guide` schreibt dort. Der gültige Stand steht in `netexRealisationGuideSwitzerland.lock.json`.
- Eigener Code liegt nur in `netex-ch-explorer/`. Guide-Dateien nie hierher kopieren, auch nicht nach `fixtures/`; `fixtures/` enthält nur selbst erstellte Testdaten.
- Pfade zu `netexRealisationGuideSwitzerland` und `netex-files` nur über die Konfiguration (Standard `../netexRealisationGuideSwitzerland`, `../netex-files`), nie fest im Code.
- Der Adapter „CH 2.0“ ist eigener Code. Er belegt jede fachliche Regel in `docs/mapping.md` mit Guide-Datei und Commit.

## Grundsätze

- **Klein und wartbar vor ausgefeilten Funktionen.** Die einfachste Lösung, die die Anforderung erfüllt, hat Vorrang.
- **Aufwand offenlegen:** Bedeutet eine Anforderung viel Code oder eine komplexe Lösung, sage ich das *vor* der Umsetzung, mit grober Einschätzung und einfacherer Alternative. Das gilt besonders, wenn der Nutzen fraglich ist. Der Benutzer entscheidet.
- **Unklarheiten und Widersprüche** (im Plan, in Entscheidungen, im Guide oder in den Daten) nicht selbst auflösen, sondern dem Benutzer vorlegen und gemeinsam klären. Danach in `docs/decisions.md` festhalten.

## Arbeitsregeln

- **Keine Lieferdaten in den LLM-Kontext.** Grosse Lieferungen (z. B. `../netex-files/`, 12 GB) nur lokal per Skript auswerten. In den Kontext kommen nur zusammengefasste Ausgaben (Zählungen, Strukturen, Messwerte). Nie ganze Dateien lesen. Ob einzelne kleine Ausschnitte erlaubt sind, ist noch offen; bis dahin nur gezielt und sparsam. Die kleinen Beispieldateien des Guide-Repos sind öffentliche Dokumentation und von dieser Regel nicht betroffen.
- Entwicklung und automatisierte Tests auf den Guide-Beispielen und kleinen synthetischen Fixtures.
- Heruntergeladene Daten liegen in einem eigenen Ordner. Python, das sie liest, mit `python3 -I` ausführen. Code aus dem Guide-Repo nicht ungeprüft ausführen.
- NeTEx-Daten nie erfinden oder ergänzen; nicht Auflösbares explizit kennzeichnen.
- **Echte Bezeichnungen verwenden:** Fremde Quellen heissen im Projekt so wie im Original, z. B. Ordner `netexRealisationGuideSwitzerland` nach dem GitHub-Repo `openTdataCH/netexRealisationGuideSwitzerland`. Keine eigenen Kurznamen erfinden.
- Technische Vorgaben des Plans dürfen hinterfragt werden. Abweichungen gemeinsam mit dem Benutzer festlegen.
- **Offene Punkte einzeln klären:** genau eine Frage bzw. ein Punkt pro Nachricht. Erst wenn er geklärt und in `docs/decisions.md` eingetragen ist, folgt der nächste.
- Neue Entscheidungen in `docs/decisions.md` eintragen, neue Rechercheergebnisse unter `docs/research/`. Diese Datei bleibt kurz.

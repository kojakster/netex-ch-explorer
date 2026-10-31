# NeTEx CH Explorer

Lokales Werkzeug, um Schweizer NeTEx-Dateien visuell und selbsterklärend zu verstehen: Fahrt als Fahrplan, Herkunft jeder Angabe bis zur Stelle im XML, Frame-Farben, Objekte und Verweise, Fehler mit Guide-Verweis.

> **Stand:** In Vorbereitung. Bisher sind nur Planung und Einrichtung des CH-NeTEx-Guides vorhanden; Installation und Start der Anwendung folgen mit der Umsetzung (siehe [UMSETZUNGSPLAN.md](UMSETZUNGSPLAN.md)).

## Ordnerstruktur

```text
NeTEx-Viewer/                          Sammelordner
├── netexRealisationGuideSwitzerland/  Git-Klon des CH-NeTEx-Guides (Branch next) inkl. XSD
├── netex-files/                       NeTEx-Lieferdaten (optional, nicht im Workspace)
└── netex-ch-explorer/                 dieses Projekt
```

## Einrichtung

### Voraussetzungen

- Git

Weitere Voraussetzungen für die Anwendung folgen mit der Umsetzung.

### CH-NeTEx-Guide klonen (einmalig)

Der Guide liegt **neben** diesem Projekt im Ordner `netexRealisationGuideSwitzerland`. Die XSD ist im Guide ein Git-Submodul und wird beim Klonen **nicht** automatisch mitgeladen; deshalb der zweite Befehl.

**macOS** (Terminal; Pfad an den eigenen Sammelordner anpassen):

```bash
cd /Users/hildebrandb/dev/NeTEx-Viewer
git clone --branch next https://github.com/openTdataCH/netexRealisationGuideSwitzerland.git netexRealisationGuideSwitzerland
cd netexRealisationGuideSwitzerland
git submodule update --init --depth 1
```

**Windows** (PowerShell; `C:\Pfad\zu\NeTEx-Viewer` durch den eigenen Sammelordner ersetzen):

```powershell
cd C:\Pfad\zu\NeTEx-Viewer
git clone --branch next https://github.com/openTdataCH/netexRealisationGuideSwitzerland.git netexRealisationGuideSwitzerland
cd netexRealisationGuideSwitzerland
git submodule update --init --depth 1
```

`--depth 1` lädt von der XSD nur den benötigten Stand statt der ganzen Geschichte des NeTEx-Repositorys. Getestet am 31.10.2026: Guide-Commit `b7ac158`, XSD `73b337e`, rund 130 MB.

### Prüfen

Im Ordner `netexRealisationGuideSwitzerland` (macOS und Windows gleich):

```bash
git branch --show-current          # erwartet: next
git log -1 --format="%h %cd"       # zeigt den Guide-Stand
git submodule status               # erwartet: Zeile mit "xsd"
```

Zusätzlich muss die Datei `xsd/xsd/NeTEx_publication.xsd` existieren, und in `src/examples/` liegen die Beispiel-XML-Dateien.

### Guide aktualisieren

Im Ordner `netexRealisationGuideSwitzerland`:

```bash
git pull
git submodule update --init --depth 1
```

Die Dateien im Guide-Ordner nie von Hand ändern.

### VS-Code-Workspace

In VS Code **Datei → Arbeitsbereich aus Datei öffnen…** wählen und `netex-ch-explorer/netex-ch-explorer.code-workspace` öffnen. Projekt und Guide erscheinen nebeneinander. `netex-files/` ist bewusst nicht enthalten (sehr gross).

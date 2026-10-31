# NeTEx CH Explorer

Lokales Werkzeug, um Schweizer NeTEx-Dateien visuell und selbsterklärend zu verstehen: Fahrt als Fahrplan, Herkunft jeder Angabe bis zur Stelle im XML, Frame-Farben, Objekte und Verweise, Fehler mit Guide-Verweis.

> **Stand:** Phase 0 (Grundgerüst) des [UMSETZUNGSPLAN.md](UMSETZUNGSPLAN.md). Die Anwendung startet, zeigt den Guide-Stand, die Farblegende und die Hilfeseite. Beispiele laden, Fahrtansicht und Prüfungen folgen in den nächsten Phasen. Unter Windows noch **nicht getestet**.

## Ordnerstruktur

```text
NeTEx-Viewer/                          Sammelordner
├── netexRealisationGuideSwitzerland/  Git-Klon des CH-NeTEx-Guides (Branch next) inkl. XSD
├── netex-files/                       NeTEx-Lieferdaten (optional, nicht im Workspace)
└── netex-ch-explorer/                 dieses Projekt
```

## Einrichtung

### Voraussetzungen

- **Git**
- **uv** (Python-Umgebung und -Pakete; installiert bei Bedarf Python 3.13 selbst): https://docs.astral.sh/uv/getting-started/installation/
- **Node.js 22** mit npm (für die Oberfläche): https://nodejs.org/

Auf macOS sind alle drei bereits eingerichtet. Unter Windows einmalig installieren (siehe [Windows-Testanleitung](#windows-testanleitung)).

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

### Projekt einrichten (einmalig)

Im Ordner `netex-ch-explorer` (macOS und Windows gleich):

```bash
uv sync
git config core.hooksPath .githooks
```

`uv sync` legt die Python-Umgebung `.venv` mit den Paketen aus `uv.lock` an. Der zweite Befehl aktiviert den Git-Hook, der vor jedem Commit den Prüfbefehl ausführt. Die Pakete der Oberfläche (`app/frontend/node_modules`) installiert das Start-Skript beim ersten Start selbst (`npm ci`).

### VS-Code-Workspace

In VS Code **Datei → Arbeitsbereich aus Datei öffnen…** wählen und `netex-ch-explorer/netex-ch-explorer.code-workspace` öffnen. Projekt und Guide erscheinen nebeneinander. `netex-files/` ist bewusst nicht enthalten (sehr gross).

## Start

Im Ordner `netex-ch-explorer`:

| System | Befehl |
|---|---|
| macOS | `./start.sh` |
| Windows (PowerShell) | `.\start.ps1` |
| beide | `uv run python scripts/start.py` |

Das Skript baut die Oberfläche, wenn sie fehlt oder veraltet ist, startet den Server auf `http://127.0.0.1:8765/` und öffnet den Browser. Beenden mit **Ctrl+C**. Optionen: `--port 9000`, `--no-browser`.

Nach einem Guide-Update (`git pull` im Guide-Ordner) die Anwendung neu starten; die Guide-Status-Box meldet dann „weicht vom zuletzt getesteten Stand ab“, bis die Tests mit dem neuen Stand gelaufen sind.

## Einstellungen

Im Ordner `config/` (JSON, UTF-8). Fehlt eine Datei oder ist ein Eintrag ungültig, gilt der Standardwert; die Oberfläche zeigt dann unter „Einstellungen“ einen Hinweis.

| Datei | Inhalt |
|---|---|
| `settings.json` | `guidePath` (Standard `../netexRealisationGuideSwitzerland`), `netexFilesPath`, `language` (`de-CH` oder `en`), `port`, `zipLimits` |
| `frame-colors.json` | Farbe und Schriftfarbe je Frame (`#RRGGBB`) |
| `not-relevant-elements.json` | Elementtypen, die samt Inhalt grau („für den Fahrplan nicht relevant“) erscheinen |

## Tests und Prüfbefehl

| Befehl | Zweck |
|---|---|
| `uv run python scripts/test.py` | Alle Python-Tests, auch gegen den Guide-Klon (dort Pflicht). Bei Erfolg schreibt das Skript `guide-tested.json` mit dem getesteten Guide- und XSD-Commit. Mit eigenen pytest-Argumenten (z. B. `-k`) gilt der Lauf als Teillauf und schreibt nichts. |
| `uv run python scripts/check.py` | Prüfbefehl: Lockfile, ruff, mypy --strict, pytest mit Abdeckung ≥ 90 % für `app/core`, TypeScript, Biome, Vitest, Build, pip-audit, npm audit, Git-Hook aktiv. Läuft vor jedem Commit über den Git-Hook (rund 15 s); der Hook verlangt zusätzlich, dass alle Änderungen vorgemerkt sind (`git add`), damit genau der Commit-Inhalt geprüft wird. `pip-audit` und `npm audit` brauchen eine Internetverbindung. |
| `uv run pytest` | Nur die Python-Tests (ohne Testnachweis). |
| `npm run test` (in `app/frontend`) | Nur die Frontend-Tests. |

`git commit --no-verify` ist verboten (Projektregel).

## Windows-Testanleitung

Für den ersten Test an einem Windows-PC (Windows gilt bis dahin als „nicht getestet“):

1. Installieren: Git (https://git-scm.com/download/win), uv (PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`), Node.js 22 LTS (https://nodejs.org/). PowerShell danach neu öffnen.
2. Sammelordner anlegen, Guide klonen wie oben unter „CH-NeTEx-Guide klonen“ beschrieben, das Projekt `netex-ch-explorer` daneben ablegen.
3. Im Ordner `netex-ch-explorer`: `uv sync` und `git config core.hooksPath .githooks`.
4. Falls PowerShell das Skript blockiert: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
5. `.\start.ps1` ausführen. Prüfen: Browser öffnet sich; links oben steht der Guide-Stand mit Branch `next`, Commit, XSD „vorhanden“, Mappingtabelle „8 Blätter gelesen“; die Farblegende ist sichtbar; „Hilfe“ öffnet die Hilfeseite; Sprache auf English umschalten.
6. `uv run python scripts/test.py` und `uv run python scripts/check.py` ausführen; beide müssen grün enden.
7. Ergebnis (inkl. Fehlermeldungen) im Testbericht `docs/test-report.md` festhalten.

## Bekannte Grenzen

- Phase 0: noch keine Beispiele, keine eigenen Dateien, keine Fahrtansicht, keine Prüfungen (die Hilfeseite listet sie als „nicht durchgeführt“).
- Kein Commit-Datum des Guides (bewusst, siehe `docs/decisions.md`).
- Der Guide-Status wird beim Start ermittelt; nach einem Guide-Update neu starten.
- Windows: noch nicht getestet.

# NeTEx CH Explorer

Lokales Werkzeug, um Schweizer NeTEx-Dateien visuell und selbsterklärend zu verstehen: Fahrt als Fahrplan, Herkunft jeder Angabe bis zur Stelle im XML, Frame-Farben, Objekte und Verweise, Fehler mit Guide-Verweis.

> **Stand:** Phase 4 (Eigene Dateien und Validierung) des [UMSETZUNGSPLAN.md](UMSETZUNGSPLAN.md). Die Anwendung zeigt den Guide-Stand, lädt jedes Beispiel des Guides, listet Fahrten, sucht Objekte, zeigt jedes Objekt mit Frame, Stelle, Verweisen vor und zurück und exakter Markierung im XML, und zeigt jede Fahrt als Fahrplan: Halte in XML-Reihenfolge, berechnete Zeiten mit Rechenkette, Tageswechsel, Betriebstage, Angebote, Teilstrecken und Hinweise, jede Angabe mit Herkunft. Eigene Dateien (XML, mehrere XML oder ZIP) öffnet der Dialog „Datei öffnen“; das Tool erkennt ihre Version und prüft CH-2.0-Dateien mit XSD, den allgemeinen Guide-Regeln und den Schweizer Kernregeln für den Fahrplan (Ergebnis „geprüft gegen Entwurf <Commit>“). Unter Windows noch **nicht getestet**.

## Ordnerstruktur

```text
NeTEx-Viewer/                          Sammelordner
├── netexRealisationGuideSwitzerland/  Git-Klon des CH-NeTEx-Guides (Branch next) inkl. XSD
├── netex-files/                       NeTEx-Lieferdaten (optional, nicht im Workspace)
└── netex-ch-explorer/                 dieses Projekt
```

## Installation

Schritt für Schritt für einen neuen Rechner. Befehle für **macOS** im Programm *Terminal*, für **Windows** in der *PowerShell*. Den Pfad zum Sammelordner jeweils an den eigenen Rechner anpassen (Beispiele: `~/dev/NeTEx-Viewer` bzw. `C:\dev\NeTEx-Viewer`).

### 1. Voraussetzungen installieren (einmalig)

| Programm | Wofür | Version |
|---|---|---|
| **Git** | Projekt und Guide holen und aktualisieren | aktuell |
| **uv** | Python-Umgebung und -Pakete; holt Python 3.13 bei Bedarf selbst | aktuell |
| **Node.js** mit npm | Oberfläche bauen und prüfen (nicht für den Betrieb) | 22 |

**macOS** (mit Homebrew, https://brew.sh):

```bash
# Homebrew, falls noch nicht vorhanden
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install git uv node@22
# node@22 wird von Homebrew nicht automatisch in den PATH gelegt:
echo 'export PATH="$(brew --prefix node@22)/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Windows** (PowerShell):

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
```

Node.js 22: Installer „v22 LTS, Windows Installer (.msi)“ von https://nodejs.org/en/download herunterladen und ausführen. Danach **PowerShell schliessen und neu öffnen**, damit die neuen Programme gefunden werden.

Falls `winget` fehlt: Git von https://git-scm.com/download/win installieren und uv mit
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.

**Prüfen** (macOS und Windows gleich):

```bash
git --version     # git version 2.x
uv --version      # uv 0.x
node --version    # v22.x
npm --version     # 10.x oder neuer
```

### 2. Sammelordner anlegen und Projekt holen

**macOS:**

```bash
mkdir -p ~/dev/NeTEx-Viewer
cd ~/dev/NeTEx-Viewer
```

**Windows:**

```powershell
New-Item -ItemType Directory -Force C:\dev\NeTEx-Viewer
cd C:\dev\NeTEx-Viewer
```

Das Projekt muss danach als Ordner `netex-ch-explorer` im Sammelordner liegen:

- **Aus einem Git-Repository** (sobald eines eingerichtet ist; die URL nennt, wer es verwaltet):
  `git clone <URL des Projekt-Repositorys> netex-ch-explorer`
- **Ohne Repository:** den Ordner `netex-ch-explorer` vollständig in den Sammelordner kopieren (inklusive des versteckten Ordners `.git`). Nicht mitkopieren müssen `.venv`, `app/frontend/node_modules` und `app/frontend/dist`; sie entstehen neu.

### 3. CH-NeTEx-Guide klonen (einmalig)

Der Guide liegt **neben** dem Projekt im Ordner `netexRealisationGuideSwitzerland`. Die XSD ist im Guide ein Git-Submodul und wird beim Klonen **nicht** automatisch mitgeladen; deshalb der zweite Befehl. Im Sammelordner (macOS und Windows gleich):

```bash
git clone --branch next https://github.com/openTdataCH/netexRealisationGuideSwitzerland.git netexRealisationGuideSwitzerland
cd netexRealisationGuideSwitzerland
git submodule update --init --depth 1
cd ..
```

`--depth 1` lädt von der XSD nur den benötigten Stand statt der ganzen Geschichte des NeTEx-Repositorys. Getestet am 31.10.2026: Guide-Commit `b7ac158`, XSD `73b337e`, rund 130 MB.

**Prüfen** im Ordner `netexRealisationGuideSwitzerland`:

```bash
git branch --show-current          # erwartet: next
git log -1 --format="%h %cd"       # zeigt den Guide-Stand
git submodule status               # erwartet: Zeile mit "xsd"
```

Zusätzlich muss die Datei `xsd/xsd/NeTEx_publication.xsd` existieren, und in `src/examples/` liegen die Beispiel-XML-Dateien.

Danach sieht der Sammelordner so aus:

```text
NeTEx-Viewer/
├── netexRealisationGuideSwitzerland/
└── netex-ch-explorer/
```

### 4. Projekt einrichten (einmalig)

Im Ordner `netex-ch-explorer` (macOS und Windows gleich):

```bash
uv sync
git config core.hooksPath .githooks
```

`uv sync` legt die Python-Umgebung `.venv` mit den Paketen aus `uv.lock` an (lädt bei Bedarf Python 3.13). Der zweite Befehl aktiviert den Git-Hook, der vor jedem Commit den Prüfbefehl ausführt. Die Pakete der Oberfläche installiert und baut das Start-Skript beim ersten Start selbst (`npm ci`, `npm run build`).

**Nur Windows:** Falls PowerShell Skripte blockiert („Ausführung von Skripts ist deaktiviert“), einmalig:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 5. Starten

Im Ordner `netex-ch-explorer`:

| System | Befehl |
|---|---|
| macOS | `./start.sh` |
| Windows (PowerShell) | `.\start.ps1` |
| beide | `uv run python scripts/start.py` |

Das Skript baut die Oberfläche, wenn sie fehlt oder veraltet ist (beim ersten Start rund eine Minute), startet den Server auf `http://127.0.0.1:8765/` und öffnet den Browser. Beenden mit **Ctrl+C**. Optionen: `--port 9000`, `--no-browser`.

Nach dem Start lädt das Tool im Hintergrund die XSD des Guides (rund 17 Sekunden) und prüft die Beispiele; die Guide-Status-Box zeigt „XSD wird geladen …", solange das läuft. Danach zeigt die Beispielliste den Status jedes Beispiels (XML-Syntax, XSD, Guide-Regeln, Kernregeln, Referenzen).

### Eigene Dateien öffnen und prüfen

1. In der linken Spalte **Datei öffnen …** wählen und im Dialog eine XML-Datei, mehrere XML-Dateien oder eine ZIP-Datei auswählen. Es gibt keine Pfadeingabe; die Dateien gehen nur an den lokalen Server und liegen im Ordner `work/` (nicht versioniert), bis ein anderer Datensatz geöffnet wird oder der Server neu startet.
2. Unter **Geöffnete Dateien** steht je Datei die erkannte Version mit Begründung (Namensraum, `version`-Attribut, `schemaLocation`, Kommentare, Dateiname, Struktur). Nur Dateien, die als CH-Profil 2.0 erkannt sind, werden geprüft; andere (z. B. NeTEx 1.10) bleiben im Explorer ansehbar.
3. **Prüfen** startet XSD-Prüfung, die Regeln von `general_rules.sch` und die Kernregeln. Befunde erscheinen unter **Diagnosen**, getrennt nach Art, mit Schweregrad, Stelle (Klick markiert sie im XML) und Link auf das Guide-Kapitel im geprüften Commit.
   Ist die Version einer Datei mehrdeutig oder unbekannt, wird sie nicht geprüft; der Knopf **Trotzdem als CH 2.0 prüfen** erzwingt die Prüfung auf ausdrücklichen Wunsch, das Ergebnis vermerkt „als CH 2.0 geprüft auf Wunsch, Version nicht erkannt“. Eine erkannte andere Version (z. B. 1.10) wird nie so geprüft.
4. Abgewiesene Dateien (falscher Typ, zu gross, unsichere ZIP-Einträge …) erscheinen als Diagnosen der Art „Datei“. Die Grenzwerte stehen in `config/settings.json` (`zipLimits`).

### 6. Funktion prüfen (optional)

```bash
uv run python scripts/test.py      # alle Tests; schreibt guide-tested.json
uv run python scripts/check.py     # alle Qualitätsprüfungen (braucht Internet)
```

Beide müssen mit „erfolgreich“ bzw. „Prüfbefehl grün“ enden.

### Guide aktualisieren

Im Ordner `netexRealisationGuideSwitzerland`:

```bash
git pull
git submodule update --init --depth 1
```

Danach die Anwendung neu starten. Die Guide-Status-Box meldet „weicht vom zuletzt getesteten Stand ab“, bis `scripts/test.py` mit dem neuen Stand gelaufen ist. Die Dateien im Guide-Ordner nie von Hand ändern.

### VS-Code-Workspace

In VS Code **Datei → Arbeitsbereich aus Datei öffnen…** wählen und `netex-ch-explorer/netex-ch-explorer.code-workspace` öffnen. Projekt und Guide erscheinen nebeneinander. `netex-files/` ist bewusst nicht enthalten (sehr gross).

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

1. [Installation](#installation) Schritte 1–4 für Windows ausführen.
2. `.\start.ps1` ausführen. Prüfen: Browser öffnet sich; links oben steht der Guide-Stand mit Branch `next`, Commit, XSD „vorhanden“, Mappingtabelle „8 Blätter gelesen“; die Farblegende ist sichtbar; Beispiel 01 anklicken, in der Fahrtenliste „ServiceJourney“ anklicken (Fahrtansicht mit drei Halten, Ankunft in Interlaken Ost 10:54 als „berechnet“; ein Klick auf die Zeit zeigt die Rechenkette), oben „Objekt“ wählen und im Inhalt `DepartureTime` anklicken: rechts ist `<DepartureTime>10:35:00</DepartureTime>` markiert; „Hilfe“ öffnet die Hilfeseite; Sprache auf English umschalten.
3. `uv run python scripts/test.py` und `uv run python scripts/check.py` ausführen; beide müssen grün enden.
4. Ergebnis (inkl. Fehlermeldungen) im Testbericht `docs/test-report.md` festhalten.

## Bekannte Grenzen

- Phase 4: Geprüft werden XML-Syntax, Referenzen, XSD, `general_rules.sch` und 30 Schweizer Kernregeln für den Fahrplan; die übrigen rund 330 Profilregeln sind noch nicht eingebunden (die Hilfeseite listet sie als „nicht durchgeführt“). Erklärungen und Korrekturvorschläge zu den Befunden folgen später. Grosse Lieferungen (12 GB) sind nicht Ziel dieser Stufe (Grenzwerte: 200 MB gesamt, 50 MB je Datei).
- Fahrtansicht: Nicht dargestellt sind Zieländerungen (`DestinationDisplay`), Formation, Flügelung, Durchbindung, Bedarfsverkehr und Takt; sie bleiben im Objekt-Explorer einsehbar. Die Angaben der Beispiele des Guides enthalten Widersprüche ([docs/assumptions.md](docs/assumptions.md)); das Tool zeigt sie, korrigiert sie aber nicht.
- Nur Dateien in UTF-8 (oder ASCII); Dateien mit `DOCTYPE` werden aus Sicherheitsgründen nicht gelesen.
- Kein Commit-Datum des Guides (bewusst, siehe `docs/decisions.md`).
- Der Guide-Status wird beim Start ermittelt; nach einem Guide-Update neu starten.
- Windows: noch nicht getestet.

# NeTEx CH Explorer

Lokales Werkzeug, um Schweizer NeTEx-Dateien visuell und selbsterklärend zu verstehen: Fahrt als Fahrplan, Herkunft jeder Angabe bis zur Stelle im XML, Frame-Farben, Objekte und Verweise, Fehler mit Guide-Verweis.

> **Stand:** Erste Ausbaustufe abgeschlossen (Phasen 0–5 des [UMSETZUNGSPLAN.md](UMSETZUNGSPLAN.md), 01.11.2026): Guide-Beispiele und eigene Dateien öffnen, Fahrtansicht mit berechneten Zeiten und Herkunft bis zur Stelle im XML, Objekt-Explorer mit Referenzen, Prüfung gegen XSD, Guide-Regeln und Schweizer Kernregeln. Unter Windows noch **nicht getestet**.

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

### 5. Starten und beenden

Im Ordner `netex-ch-explorer`:

| System | Befehl |
|---|---|
| macOS | `./start.sh` |
| Windows (PowerShell) | `.\start.ps1` |
| beide | `uv run python scripts/start.py` |

Das Skript baut die Oberfläche, wenn sie fehlt oder veraltet ist (beim ersten Start rund eine Minute; es installiert dabei die Pakete der Oberfläche mit `npm ci`), startet den Server auf `http://127.0.0.1:8765/` und öffnet den Browser. Optionen: `--port 9000` (anderer Port; der Server prüft die Herkunft der Anfragen gegen genau diesen Port und arbeitet in `work/9000/`; ist der Port belegt, bricht der Start ab, ohne etwas zu löschen), `--no-browser` (Browser nicht öffnen).

**Beenden:** im Terminal-Fenster, in dem der Server läuft, **Ctrl+C** drücken. Danach ist der Port wieder frei; Die Dateien im Arbeitsordner des Servers (`work/<Port>/`) werden beim Beenden und, falls der Server abgestürzt ist, beim nächsten Start auf demselben Port gelöscht; Ordner anderer Ports (laufende Server) bleiben unberührt. Das Schliessen des Browser-Tabs beendet den Server nicht.

Nach dem Start lädt das Tool im Hintergrund die XSD des Guides (rund 17 Sekunden) und prüft die Beispiele; der Guide-Status in der Kopfzeile zeigt (aufgeklappt) „XSD wird geladen …", solange das läuft. Danach zeigt die Beispielliste den Status jedes Beispiels (XML-Syntax, XSD, Guide-Regeln, Kernregeln, Referenzen).

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

Danach die Anwendung neu starten. Der Guide-Status in der Kopfzeile (Punkt „Guide: Abweichung“) meldet aufgeklappt „weicht vom zuletzt getesteten Stand ab“, bis `scripts/test.py` mit dem neuen Stand gelaufen ist. Die Dateien im Guide-Ordner nie von Hand ändern.

### VS-Code-Workspace

In VS Code **Datei → Arbeitsbereich aus Datei öffnen…** wählen und `netex-ch-explorer/netex-ch-explorer.code-workspace` öffnen. Projekt und Guide erscheinen nebeneinander. `netex-files/` ist bewusst nicht enthalten (sehr gross).

## Bedienung

Kurzanleitung für den ersten Test (die Hilfeseite der Anwendung erklärt alle Funktionen, Farben und Prüfungen ausführlicher):

1. **Beispiel wählen.** Nach dem Start erklärt die Startseite die Bedienung in drei Schritten und listet die Beispiele des Guides mit Beschreibung; Beispiel `01_NeTEx_Spiez_Interlaken_Ost.xml` ist als Einstieg hervorgehoben. Ein Beispiel lässt sich dort anklicken oder jederzeit in der Kopfzeile unter „Datensatz“ wählen. Jedes Beispiel zeigt seinen Prüfstatus (✔ ohne Meldungen, ℹ/⚠ mit Hinweisen oder Fehlern, ✖ nicht lesbar). Der Punkt „Guide: ok / Abweichung / Fehler“ in der Kopfzeile klappt per Klick den Guide-Stand auf; solange dort „XSD wird geladen …“ steht (rund 17 Sekunden), fehlen die Status der Beispiele; das Öffnen funktioniert trotzdem.
2. **Fahrt öffnen.** Links im Reiter „Fahrten“ die Fahrt (`ServiceJourney`) anklicken: eine Zeile pro Fahrt mit Produktkategorie und Zugnummer, darunter Abfahrt und Strecke. Der Hauptbereich zeigt sie als Fahrplan: Kopf mit Zugnummer, Linie, Verkehrsmittel und Betriebstagen, darunter die Halte mit Ein-/Aussteigen, Ankunft, Abfahrt und Angeboten. Zeiten, die nicht in der Datei stehen, sind als „berechnet“ gekennzeichnet; ein Klick auf die Zeit zeigt die Rechenkette.
3. **Halt anklicken.** Ein Klick auf eine Angabe (z. B. den Halt „Interlaken West“) wählt sie. **Rechts** erscheint dann die Spalte „Herkunft und XML“ mit der **Herkunftskette** als farbige Kästchen (z. B. `ServiceFrame` → `ScheduledStopPoint` → `Name`; jedes Kästchen ist anklickbar) und dem **XML-Ausschnitt** mit der exakt markierten Stelle (hier `<Name lang="de">Interlaken West</Name>`) und, am Rand, dem Frame mit seiner Farbe. „Schliessen“ hebt die Auswahl auf; der Hauptbereich nutzt dann die ganze Breite.
4. **Objekt ansehen.** Oben im Hauptbereich zwischen „Fahrt“ und „Objekt“ umschalten. „Objekt“ zeigt Typ, ID, Frame, Datei mit Zeile und Spalte, Inhalt und die Verweise vor und zurück (farbig nach dem Frame des Ziels, jeder anklickbar). Im Reiter „Objekte“ links lässt sich jedes Objekt der Datei suchen (Typ, Teil der ID oder des Namens). „Zurück im Verlauf“ und „Vor im Verlauf“ führen zu früheren Auswahlen.
5. **Farben.** Jeder Frame hat eine feste Farbe; die Legende steht dort, wo Farben sichtbar sind (rechte Spalte), immer mit Frame-Name. Grau heisst „für den Fahrplan nicht relevant“. Die Farben stehen in `config/frame-colors.json` und lassen sich ohne Codeänderung anpassen.
6. **Eigene Datei öffnen und prüfen:** siehe unten.
7. **Hilfe.** Oben rechts öffnet „Hilfe“ die Hilfeseite: Funktionen, Frame-Farben und Grau-Liste, durchgeführte und nicht durchgeführte Prüfungen (mit Quelle bzw. Stand), die Schweizer Kernregeln, Schweregrade (⚠ Fehler, △ Warnung, ℹ Hinweis) und der Guide-Stand. Daneben lässt sich die Sprache (Deutsch/English) umschalten.

### Eigene Dateien öffnen und prüfen

1. In der Kopfzeile **Datei öffnen …** wählen und im Dialog eine XML-Datei, mehrere XML-Dateien oder eine ZIP-Datei auswählen. Es gibt keine Pfadeingabe; die Dateien gehen nur an den lokalen Server und liegen im Ordner `work/<Port>/` (nicht versioniert), bis ein anderer Datensatz geöffnet wird oder der Server neu startet.
2. Im Reiter **Prüfung** links steht unter **Geöffnete Dateien** je Datei die erkannte Version mit Begründung (Namensraum, `version`-Attribut, `schemaLocation`, Kommentare, Dateiname, Struktur). Nur Dateien, die als CH-Profil 2.0 erkannt sind, werden geprüft; andere (z. B. NeTEx 1.10) bleiben im Explorer ansehbar.
3. **Prüfen** startet XSD-Prüfung, die Regeln von `general_rules.sch` und die Kernregeln. Befunde erscheinen im selben Reiter unter **Diagnosen** (die Beschriftung des Reiters nennt danach ihre Anzahl), getrennt nach Art, mit Schweregrad, Stelle (Klick markiert sie im XML) und Link auf das Guide-Kapitel im geprüften Commit.
   Ist die Version einer Datei mehrdeutig oder unbekannt, wird sie nicht geprüft; der Knopf **Trotzdem als CH 2.0 prüfen** erzwingt die Prüfung auf ausdrücklichen Wunsch, das Ergebnis vermerkt „als CH 2.0 geprüft auf Wunsch, Version nicht erkannt“. Eine erkannte andere Version (z. B. 1.10) wird nie so geprüft.
4. Abgewiesene Dateien (falscher Typ, zu gross, unsichere ZIP-Einträge …) erscheinen als Diagnosen der Art „Datei“. Die Grenzwerte stehen in `config/settings.json` (`zipLimits`).

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
| `npm run test` (in `app/frontend`) | Nur die Frontend-Tests (Vitest). |
| `NETEX_API_PORT=9000 npm run dev` (in `app/frontend`) | Entwicklungsserver der Oberfläche; der Proxy geht an den Server auf dem Port aus `config/settings.json`, mit `NETEX_API_PORT` an den Port, mit dem `start.py --port` gestartet wurde (PowerShell: `$env:NETEX_API_PORT="9000"; npm run dev`). |
| `npm run e2e:install` (in `app/frontend`, einmalig) | Lädt den Browser (Chromium) für den E2E-Test herunter (rund 150 MB, braucht Internet). |
| `npm run e2e` (in `app/frontend`) | E2E-Test mit Playwright: startet den Server selbst (Testport 8766, anderer Port mit `E2E_PORT`), öffnet Beispiel 01, die Fahrt und einen Halt und prüft XML-Stelle und Frame; beendet den Server danach. Ohne Guide-Klon wird der Test übersprungen (mit `NETEX_REQUIRE_GUIDE=1` schlägt er stattdessen fehl). Statt des heruntergeladenen Browsers lässt sich der installierte Chrome nutzen: `E2E_BROWSER_CHANNEL=chrome npm run e2e` (macOS/Linux) bzw. `$env:E2E_BROWSER_CHANNEL="chrome"; npm run e2e` (PowerShell). |

Der E2E-Test gehört bewusst **nicht** zum Prüfbefehl (Begründung in [docs/decisions.md](docs/decisions.md)): Er braucht einen Browser, den Guide-Klon und einen Serverstart, und der Prüfbefehl läuft vor jedem Commit. Vor einer Übergabe oder einer Änderung an der Oberfläche gehört er dazu.

`git commit --no-verify` ist verboten (Projektregel).

## Windows-Testanleitung

Für den ersten Test an einem Windows-PC (Windows gilt bis dahin als „nicht getestet“):

1. [Installation](#installation) Schritte 1–4 für Windows ausführen.
2. `.\start.ps1` ausführen. Prüfen: Der Browser öffnet sich; links oben steht der Guide-Stand mit Branch `next`, Commit, XSD „vorhanden“, Mappingtabelle „8 Blätter gelesen“; die Farblegende ist sichtbar.
3. Beispiel 01 anklicken, unter „Fahrten“ die `ServiceJourney` anklicken: Die Fahrtansicht zeigt drei Halte; die Ankunft in Interlaken Ost 10:54 ist als „berechnet“ gekennzeichnet, ein Klick auf die Zeit zeigt die Rechenkette. Auf den Halt „Interlaken West“ klicken: rechts ist in der Herkunftskette `ServiceFrame` → `ScheduledStopPoint` → `Name` zu sehen, im XML ist `<Name lang="de">Interlaken West</Name>` markiert. Oben „Objekt“ wählen und im Inhalt `DepartureTime` anklicken: rechts ist `<DepartureTime>10:35:00</DepartureTime>` markiert.
4. **Datei öffnen:** „Datei öffnen …“ wählen und eine Beispieldatei aus `..\netexRealisationGuideSwitzerland\src\examples\` (z. B. `02_NeTEx_CH_PAG_11929.xml`) auswählen: unter „Geöffnete Dateien“ steht „CH-Profil 2.0“ mit Begründung. **Prüfen** wählen: Unter „Diagnosen“ erscheinen Befunde mit Stelle (Klick markiert sie im XML) und Guide-Link.
5. „Hilfe“ öffnen (Farben, Prüfungen, Guide-Stand sichtbar); Sprache auf English umschalten.
6. Server mit **Ctrl+C** beenden (prüfen: danach ist der Port frei und `work\` leer).
7. `uv run python scripts/test.py` und `uv run python scripts/check.py` ausführen; beide müssen grün enden. Optional: `cd app\frontend; npm run e2e:install; npm run e2e` (E2E-Test; ungetestet unter Windows, besonders das Beenden des Servers).
8. Ergebnis (inkl. Fehlermeldungen) im Testbericht `docs/test-report.md` festhalten.

## Bekannte Grenzen

Vollständige Übersicht mit Herkunft: [docs/test-report.md](docs/test-report.md) („Phase 5 / Übergabe“); offene Punkte: [docs/open-points.md](docs/open-points.md); Entscheide: [docs/decisions.md](docs/decisions.md).

**Prüfung**

- Geprüft werden XML-Syntax, Referenzen, XSD, `general_rules.sch` und 30 Schweizer Kernregeln für den Fahrplan. Die übrigen rund 330 Profilregeln sind nicht eingebunden (die Hilfeseite listet sie als „nicht durchgeführt“); auch CH-SJP-08 und CH-SJ-16 sind bewusst nicht umgesetzt. Erklärungen und Korrekturvorschläge zu den XSD-Befunden fehlen (nur der Originalwortlaut).
- Nur als CH 2.0 erkannte Dateien werden geprüft; andere Versionen (z. B. NeTEx 1.10) nur auf ausdrücklichen Wunsch bei mehrdeutiger oder unbekannter Version, eine erkannte andere Version nie. Das Ergebnis heisst „geprüft gegen Entwurf <Commit>“, nie „gültig“.
- Die Beispiele des Guides enthalten Widersprüche und Verstösse (z. B. 121 Verstösse gegen „kein `order`-Attribut“ in 9 Beispielen, Kommentar von Beispiel 01 mit 10:53 statt 10:54); das Tool zeigt sie, korrigiert sie aber nicht ([docs/assumptions.md](docs/assumptions.md)).
- Eine Prüfung vor Ende des XSD-Ladens wartet bis zu 17 Sekunden. Ohne XSD (Submodul nicht geholt) ist die XSD-Prüfung „nicht durchgeführt“.

**Fahrtansicht**

- Nicht dargestellt (aber im Objekt-Explorer einsehbar): Zieländerungen (`DestinationDisplay`), Takt, Formation, Flügelung, Durchbindung, Bedarfsverkehr, Elternfahrt der Kurswagen. Die Betriebstage von Kurswagen und Elternfahrt werden nicht automatisch geprüft. Ausstattung von Haltestellen hat keine eigene Darstellung (grau).
- Die Zeitumstellung wird nur für Betriebstage mit auflistbaren `ValidDayBits` geprüft (bei 15 von 22 Beispielen weicht deren Länge ab).
- Verweise in Dateien, die nicht mit geöffnet sind, bleiben „extern oder nicht geladen“ (Hinweis, kein Fehler).

**Umfang und Leistung**

- Grosse Lieferungen (z. B. die 12-GB-Lieferung 2027 in NeTEx 1.10) sind nicht Ziel dieser Stufe: Grenzwerte 200 MB gesamt, 50 MB je Datei, 500 Dateien, Kompressionsrate 100:1; ein Upload liegt beim Annehmen bis zu 200 MB im Arbeitsspeicher; Index nur im Arbeitsspeicher; die Fahrtansicht baut sich bei jedem Abruf neu auf. Datei-Import aus einem Ordner, Index auf Festplatte und Hintergrundprozess sind zurückgestellt.
- Nur Dateien in UTF-8 (oder ASCII); Dateien mit `DOCTYPE` werden aus Sicherheitsgründen nicht gelesen; Dateien mit nur CR als Zeilenumbruch haben falsche Zeilennummern.
- Höchstens 10 Datensätze gleichzeitig offen (der älteste wird geschlossen).
- Eine Webversion (Pyodide, statische Seite) gibt es noch nicht; Veröffentlichung und Lizenz der Guide-Dateien sind offen.

**Betrieb**

- Der Guide-Status wird beim Start ermittelt; nach einem Guide-Update neu starten. Ändert ein `git pull` eine Datei bei geöffnetem Datensatz, stimmen Stellen von Befunden nicht mehr; Server neu starten.
- Kein Commit-Datum des Guides (bewusst, siehe `docs/decisions.md`). Nur ein Guide-Stand gleichzeitig; keine Einstellungsseite für Farben (Datei `config/frame-colors.json`); die Sprachdateien enthalten vorläufige Fachbegriffe (Glossar offen).
- Der Prüfbefehl braucht für `pip-audit` und `npm audit` Internet; der Build meldet ein Skriptpaket über 500 kB (CodeMirror, lokal unkritisch).
- Windows: noch nicht getestet; das gilt auch für den E2E-Test. Eine Prüfung der Einrichtung „von null“ auf einem frischen Rechner steht aus (siehe Testbericht).

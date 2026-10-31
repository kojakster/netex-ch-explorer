# Qualitätsregeln für die Umsetzung

Verbindlich für jeden Code in diesem Projekt (Benutzer, 31.10.2026): **keine Sicherheitslücken, wartbar, erweiterbar, nach Best Practice, keine Abkürzungen.** „Klein“ heisst wenig bauen; was gebaut wird, wird sauber gebaut.

Claude hält sich selbst konsequent daran und kontrolliert die Einhaltung selbst. Die Einhaltung wird technisch erzwungen (Prüfbefehl, Git-Hook) und pro Phase nachweisbar dokumentiert.

## Sicherheit

- **XML:** pyexpat ohne externe Entitäten (`SetParamEntityParsing(XML_PARAM_ENTITY_PARSING_NEVER)`), ohne DTD, ohne Netzwerkzugriff. Dateien mit `DOCTYPE` werden abgewiesen (Diagnose, kein Absturz). lxml nur mit `resolve_entities=False`, `no_network=True`, `load_dtd=False`, ohne `huge_tree`.
- **ZIP:** Zip-Slip-Schutz (Zielpfad muss im Arbeitsordner liegen), keine Symlinks, Grenzwerte für Gesamtgrösse, Einzeldatei, Anzahl und Kompressionsrate (`config/settings.json`); Entpacken nur in `work/`.
- **Server:** nur `127.0.0.1`; CORS nur für das eigene Frontend; Grössenlimit für Uploads; Dateinamen bereinigt; die API nimmt **keine Dateipfade** entgegen, nur eigene, nicht erratbare IDs; einheitliche Fehlerantworten ohne interne Details (keine Stacktraces an den Client).
- **Oberfläche:** XML und Datenwerte immer als Text darstellen, nie als HTML einfügen (kein `dangerouslySetInnerHTML`, kein `innerHTML` mit Daten); strenge Content-Security-Policy; keine externen Ressourcen (Schriften, Skripte, CDNs) zur Laufzeit.
- **Abhängigkeiten:** so wenige wie möglich, Versionen in `uv.lock` und `package-lock.json` festgeschrieben; Prüfung auf bekannte Sicherheitslücken mit `pip-audit` und `npm audit` im Prüfbefehl.
- **Geheimnisse:** keine Zugangsdaten, Tokens oder Schlüssel im Code oder in Dateien des Repos.
- **Sicherheitstests** für XXE, `DOCTYPE`, Zip-Slip, ZIP-Grenzwerte, unzulässige Pfade/IDs, HTML in XML-Werten.

## Wartbarkeit

- **Typen:** Python mit vollständigen Typangaben, geprüft mit `mypy --strict`; TypeScript im `strict`-Modus, kein `any` ohne begründete Ausnahme.
- **Stil:** `ruff` (Prüfung und Formatierung) für Python, `Biome` (Prüfung und Formatierung) für das Frontend; Konfiguration im Repo.
- **Schichten:** `app/core` importiert weder `app/server` noch Frontend-Code; ein Test prüft diese Richtung. Die Server-Schicht bleibt dünn.
- **Code:** kleine, klar benannte Funktionen; Docstrings für öffentliche Funktionen und Module; kein toter oder auskommentierter Code; keine `TODO` ohne Eintrag in `docs/open-points.md`.
- **Fehlerbehandlung:** kein pauschales `except:`/`except Exception:` ohne erneutes Auslösen oder gezielte Diagnose; Fehler aus Daten werden zu Diagnosen mit Übersetzungsschlüssel; Programmfehler werden nicht verschluckt.
- **Protokollierung:** Python-`logging`, kein `print` im Anwendungscode.
- **Konfiguration:** wird beim Laden geprüft; ungültige Werte → Standardwert + Hinweis.
- **Ausnahmen von Prüfregeln** (z. B. `# noqa`, `# type: ignore`, Biome-Ignore) nur mit kurzer Begründung direkt daneben und Eintrag in `docs/decisions.md`.

## Erweiterbarkeit

- **CH-Versionen** als Adapter mit gemeinsamer Schnittstelle (generisch, CH 2.0, später weitere).
- **Prüfungen** als Liste von Prüfschritten (XSD, `general_rules.sch`, Kernregeln, später weitere), jeder mit Kennung, Quelle und Hilfetext.
- **Funktionen** in einer Liste, aus der die Hilfeseite erzeugt wird.
- **Farben, Grau-Liste, Pfade, Grenzwerte** in `config/`; **Texte** in Sprachdateien.
- Neue Adapter, Prüfschritte oder Sprachen sollen möglichst ohne Änderung bestehenden Codes hinzukommen.

## Tests

- Jede öffentliche Funktion des Kerns ist getestet; **Mindestabdeckung `app/core`: 90 % Zeilen**, im Prüfbefehl erzwungen.
- Server: Tests für jeden Endpunkt inkl. Fehlerfällen. Frontend: Vitest für Logik und Komponenten mit Verhalten; ein E2E-Pfad mit Playwright.
- Tests sind deterministisch und unabhängig von Netzwerk und Uhrzeit.

## Ablauf und Selbstkontrolle

1. **Prüfbefehl `scripts/check.py`** führt aus: `ruff` (Prüfung + Formatierung), `mypy --strict`, `pytest` mit Abdeckung ≥ 90 % für `app/core`, Schichtentest, Hilfeseiten-Test, Frontend-Typprüfung, `Biome`, Vitest, `pip-audit`, `npm audit`. **Muss vor jedem Commit grün sein.**
2. **Git-Hook** (`pre-commit`, im Repo unter `.githooks/`, aktiviert mit `git config core.hooksPath .githooks`) ruft `scripts/check.py` auf. **`--no-verify` ist verboten.** Schnelle Teilprüfung im Hook, vollständige Prüfung vor Phasenabschluss, falls die volle Prüfung zu lange dauert; die Aufteilung wird in `docs/decisions.md` festgehalten.
3. **Vor jedem Phasenabschluss:** Code-Review und Sicherheits-Review über die Änderungen der Phase (eingebaute Prüfungen von Claude Code), alle Funde beheben oder begründet dem Benutzer vorlegen.
4. **Nachweis pro Phase** in `docs/test-report.md`: Ergebnis des Prüfbefehls, Abdeckung, Ergebnis der Reviews mit behobenen Funden, offene Lücken. Keine Phase gilt ohne diesen Nachweis als erledigt.
5. Kleine, nachvollziehbare Commits mit aussagekräftiger Nachricht.
6. Weicht etwas von diesen Regeln ab (z. B. weil ein Werkzeug unter Windows nicht läuft), wird das dem Benutzer vorgelegt, nicht stillschweigend umgangen.

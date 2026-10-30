# CH-Profil 2.0 (Entwurf, NeTEx 2.1): Rechercheergebnisse

Stand 30.10.2026. Per Skript verifiziert an einem flachen Klon des Branches `next`.

## Quellen

- Guide (Webseite): https://opentdatach.github.io/netexRealisationGuideSwitzerland/main/index.html. Release Candidate 1 vom 07.09.2026, Release geplant 2026-11. Die Seite `…/main/…` entspricht möglicherweise einem älteren Stand.
- Repository: https://github.com/openTdataCH/netexRealisationGuideSwitzerland
  - Default-Branch `next` = `b7ac158` (Commit vom 27.10.2026); `main` = `3b5c0d2`.
  - Keine Releases; Lizenz nicht angegeben; Kontakt info.fachbus@sbb.ch.
- Echte Lieferungen im Profil 2.0 gibt es noch nicht, weil NeTEx 2.1 selbst noch in Entwicklung ist. Auch das SKI+-Handout vom 25.03.2026 nennt keinen Termin: https://www.oev-info.ch/sites/default/files/2026-04/2026_03_25_Handout_NeTEx.pdf
- Weitere CH-Profildokumente (für spätere Adapter, nicht geprüft): Profil 1.0.0 https://www.oev-info.ch/sites/default/files/2024-05/NeTEx_Core-Realisation_Guide_TP_Suisse-v1.00.pdf

## Bereitgestellte Artefakte (Branch `next`, ~23 MB ohne XSD)

| Pfad | Inhalt | Verwendung im Explorer |
|---|---|---|
| `src/examples/*.xml` | 22 Beispiele (4–56 KB) + `README.md` | Hauptdaten für Fahrtansicht, Tests und Abnahme |
| `src/templates/*.xml` | 74 Templates pro Element (z. B. `ServiceJourney.xml`, `TimeDemandType.xml`); Datei-Skelette `ch-profile_SINGLE_FILE`, `_NETWORK_OFFER`, `_SITE_OFFER`, `_INTERCHANGE`; einige `*_deprecated.xml` | Referenz für erlaubte Elemente pro Objekttyp; Erkennung des Dateityps |
| `src/schematron_rules/general_rules.sch` | Allgemeine Schematron-Regeln (1,7 KB). Weitere Schematrons erzeugt der Build aus den Templates (Ausgabe `site/`, nicht im Repo) | Profilprüfung |
| `xsd` (Submodul) | NeTEx-CEN, Branch `v2.1-wip`, gepinnt auf `73b337e` | XSD-Prüfung gegen Entwurf |
| `src/*.md` | Kapitel 01–09, Use Cases uc01–uc13 ff., Annexe A1–A6 (A6: Migration 1.0 → 2.0, „work in progress“) | Fachliche Belege für `docs/mapping.md` |
| `src/media/Mappingtabellen_NeTEx_v2.0.xlsx` | Mapping-Tabellen (Notices, ProductCategory, Facilities) | Codelisten/Anzeigetexte |
| `tools/`, `pyproject.toml` | Python-Build-Tools des Guides | Nur lesen; nicht ohne Prüfung ausführen |

## Lieferstruktur laut Guide (`src/02_files.md`)

- Dateitypen:
  - **`NETWORK_OFFER`**: Linien, Routen, Fahrpläne; ggf. mehrere Dateien.
  - **`INTERCHANGE`**: Anschlüsse, Flügelungen, Durchbindungen.
  - **`STOP_OFFER`**: so im Text; die Templates heissen `SITE_OFFER` (Inkonsistenz im Guide).
  - `SINGLE_FILE`: nur als Template vorhanden.
- SKI liefert ein SITE/STOP_OFFER, mehrere NETWORK_OFFER, ein INTERCHANGES-XML und eine README-Datei mit dem Inhalt jeder XML-Datei.
- ZIP-Name, Beispiel: `TEST_NETEX_TT_2.0_CHE_SKI_2026_OEV-SCHWEIZ_202602010402.zip`.
- INTERCHANGE ist laut Guide nur dann XSD-valide, wenn `versionRef` statt `version` verwendet wird.

## Datenmodell der Beispiele

- **Haltefolge und Zeiten:** Alle 22 Beispiele verwenden **`ServiceJourneyPatternRef` → `StopPointInJourneyPattern`** sowie **`DepartureTime` + `TimeDemandTypeRef`** (`JourneyRunTime`/`JourneyWaitTime` je `TimingLink`). Kein Beispiel nutzt `TimetabledPassingTime` oder `Call`. Die Templates `TimetabledPassingTime_deprecated.xml` und `ServiceJourney_PassingTime_deprecated.xml` sind als veraltet markiert.
- **Widerspruch Dokumentation/Dateien:** `examples/README.md` erwähnt noch „PassingTimes“ (Beispiele 02, 07). Massgebend sind die Dateien; den Widerspruch in `docs/assumptions.md` festhalten.
- **Zeiten an den Halten werden berechnet.** Die Herkunftsanzeige muss die Rechenkette als „abgeleitet“ zeigen, jeden Summanden mit eigener Quelle.
- Alle Frames in einer Datei; IDs mit `version="1"`, teils lokale IDs (`sjp1`, `tdt-1`).
- **Dieselbe ID für verschiedene Typen:** `ch:1:sloid:7483:0:90840` ist `Quay` **und** `ScheduledStopPoint`. Referenzen deshalb immer über (ID, erwarteter Typ) auflösen; den Typ aus dem Namen des Ref-Elements bzw. aus `nameOfRefClass` ableiten.
- **Wurzelattribut `version`:** 19 Beispiele `"2.1"`, 2 noch `"1.09"` (u. a. 01), 08 weicht ab. `schemaLocation` ist relativ (`../../xsd/xsd/NeTEx_publication.xsd`). Das Wurzelattribut allein taugt nicht zur Versionserkennung.
- **Fälle, die die Fahrtansicht abdecken muss** (je ein Beispiel):
  - Facilities nur auf Teilstrecken bzw. an einzelnen Tagen (08, `JourneyPart`)
  - Flügelzug (06, 13)
  - Durchbindung (07)
  - Kurswagen (19, 21)
  - Formation (20)
  - Taktlinie (12)
  - Bedarfsverkehr DRT (04, 05)
  - Zieländerung (10)
  - Zugnummernwechsel (11)
  - Teillinien/Subunternehmer (22)
  - Perron/sloid-Problem (09)

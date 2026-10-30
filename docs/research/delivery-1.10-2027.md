# Lieferung 2027 (NeTEx 1.10, „SBBSplitted“): Rechercheergebnisse

Stand 30.10.2026. Ausgewertet lokal per Streaming-Skript; nur zusammengefasste Ergebnisse.

## Quelle und Umfang

- Lokal: `../netex-files/prod_netex_tt_1.10_che_ski_2027_oev-schweiz__1_1_202610280910/`
- Herkunft: https://data.opentransportdata.swiss/dataset/timetablenetex_2027. Die Seite nennt die Lieferung „erster Testdatensatz“; Fahrplan 13.12.2026–11.12.2027; ZIP 240 MB.
- **205 XML-Dateien, 12 GB** entpackt. Das entspricht einer Kompression von ~50:1, was für die Grenzwerte gegen ZIP-Bomben relevant ist. Grösste Datei 208 MB.
- Aufteilung:
  - `…_COMMON_1_1_…`, `_RESOURCE_`, `_SERVICECALENDAR_`, `_SERVICE_`, `_SITE_`
  - `_TIMETABLE_<n>_200_…` (200 Stück)
  - `Workflow/…_README.csv` ordnet jede TIMETABLE-Datei Linie, Betreiber und Produktcode zu (3294 Zeilen; Spalten `FileName;Line;Operator;OperatorCode;ProductCode`).
- Kopf jeder Datei:
  - `version="1.10"`, `schemaLocation=http://netex.uk/netex/schema/1.10/xsd/NeTEx_publication.xsd`
  - Kommentar `<!--Profile: SBBSplitted-->`
  - `ParticipantRef MENTZ`, `Description` „NeTEx Export, Version: 19.87.0.7150“
  - Dateien beginnen mit UTF-8-BOM.
- **Frames:** Pro Datei ein Frame unter `CompositeFrame`. Frame-IDs wiederholen sich: `ch:1:TimetableFrame:j27` steht in 201 Dateien (COMMON + alle TIMETABLE). Eindeutig ist ein Frame nur als Paar (Datei, Frame-ID).
- **Versionen:** Alle Objekte haben `version="any"`. Referenzen tragen meist `versionRef`, `OperatorRef` aber `version`.

## Datenmodell (verifiziert)

- **Fahrt:** `ServiceJourney` (TimetableFrame) mit `calls/Call`. Ein `Call` enthält `order`, `ScheduledStopPointRef`, `Arrival/Time`, `Departure/Time`, `ForBoarding`/`ForAlighting` und `DestinationDisplayRef`. Dazu kommen an der Fahrt `LineRef`, `OperatorRef`, `TransportMode`, `TypeOfProductCategoryRef`, `TrainNumberRef`, `VehicleTypeRef` und `noticeAssignments`.
- **Nicht vorhanden** (in keiner der 205 Dateien): `JourneyPattern`, `ServiceJourneyPattern`, `StopPointInJourneyPattern`, `TimetabledPassingTime`, `JourneyPatternRef`, `Route`.
- **Haltestellenkette:** `Call` → `ScheduledStopPoint` (SERVICE) → `PassengerStopAssignment` (SERVICE; `StopPlaceRef` und/oder `QuayRef`) → `StopPlace`/`Quay` (SITE). Beispiel: `ch:2:ScheduledStopPoint:8508350-0-Gen` (Brienz BRB) → `ch:2:StopPlace:8508350`.
- **Verkehrstage:** `validityConditions/AvailabilityConditionRef` → `AvailabilityCondition` (SERVICECALENDAR) mit `FromDate`/`ToDate` und `ValidDayBits` (ein Bit pro Tag ab `FromDate`). Die 18 `DayType` sind nur Feiertage und werden von keiner Fahrt referenziert.
- **Angebote:**
  - Die Referenz steckt in `ServiceJourney/Extensions/facilities/Facility/ServiceFacilitySetRef`, also in einer Erweiterung.
  - Ziel ist `ServiceFacilitySet` im **TimetableFrame der COMMON-Datei** (23 Sets).
  - Nur 2 Sets haben `<FareClasses>` (z. B. `firstClass`); sonst steht die Bedeutung nur in `Description` („Nur 2. Klasse“).
- **Weitere Objekttypen:**
  - Taktfahrten: `TemplateServiceJourney`, `HeadwayJourneyGroup`
  - `TrainNumber`, `Notice`/`NoticeAssignment`, `DestinationDisplay`, `TypeOfProductCategory`, `TypeOfService`, `Line`, `Operator`, `ResponsibilitySet`, `VehicleType`
  - in COMMON zusätzlich `InterchangeRule`, `JourneyMeeting`
  - in SERVICE `SiteConnection`, `DefaultConnection`
- **Doppelte IDs kommen real vor:** TIMETABLE_1 enthält 2239 doppelte IDs (z. B. mehrere `NoticeAssignment` mit identischer ID).
- **Mengen:**
  - SERVICE/SITE: 3294 `Line`, je 56'624 `ScheduledStopPoint` und `PassengerStopAssignment`, 28'706 `StopPlace`, 43'575 `Quay`.
  - TIMETABLE_1 (34 MB): 4828 `ServiceJourney`, 28'408 `Call`.

## Versionsangaben (nicht vermischen)

- Die Lieferung nennt NeTEx 1.10. Die Datensatzseite verlinkt das Profil-PDF https://www.oev-info.ch/sites/default/files/2023-04/netex_core-realisation_guide_tp_suisse-v0.8.8.4.pdf. Dessen Titelblatt nennt jedoch „V 0.8.7.9, 26.11.2019, on the base of schema 1.08“ (381 Seiten, fr-CH).
- Der Datensatz 2026 (https://data.opentransportdata.swiss/de/dataset/timetablenetex_2026) ist ebenfalls NeTEx 1.10. Ein Vergleich damit ist nur ein Vergleich der Fahrplanjahre.
- Die Versionserkennung kombiniert mehrere Hinweise:
  - Kommentare: lxml braucht dafür das Event `comment`; Pythons Standard-`iterparse` ignoriert Kommentare.
  - `schemaLocation`, Exporter-Angaben, Dateinamenmuster und Struktur.

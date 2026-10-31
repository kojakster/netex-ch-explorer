# Synthetische Testdateien

Alle Dateien in diesem Ordner sind **selbst erstellt und synthetisch** (Projekt netex-ch-explorer, 31.10.2026). Sie enthalten **keine echten Fahrplandaten** und keine Kopien von Guide-Dateien. Aufbau und Elementreihenfolge folgen dem CH-Profil 2.0 (Guide `b7ac158`, XSD `73b337e`), die Inhalte sind erfunden und als synthetisch gekennzeichnet: Kopfkommentar „SYNTHETISCHE TESTDATEN“, `ParticipantRef` `SYNTHETIC`, Namen „Synthetisch …“, IDs mit `SYN`. Die Dateien dürfen frei weitergegeben werden. Das Tool darf sie nie als echte Fahrplandaten ausgeben.

| Datei | Zweck | XSD (NeTEx 2.1, `73b337e`) |
|---|---|---|
| `ch20_three_stops.xml` | Grunddatei: Fahrt SYN 1 mit drei Halten, alle Frames in einer Datei; `Quay` und `ScheduledStopPoint` mit gleicher ID. Zeiten: A ab 08:00, B an 08:10 / ab 08:12, C an 08:27 (berechnet). Betriebstage 14.–18.12.2026 (`ValidDayBits` `0111110`). Mit `TypeOfProductCategory` (`SYN`) und Verweis, damit die Datei alle Schweizer Kernregeln erfüllt (XSD gültig, keine Kernregel-Verstösse). | gültig |
| `ch20_offers.xml` | Angebote, Teilstrecke, Hinweise und Stammdaten: Fahrt SYN 1 wie in `ch20_three_stops.xml`, dazu `TypeOfProductCategory` (`SYN`), `TransportSubmode`, `RequestStop`/`StopUse`, ein `ServiceFacilitySet` für die ganze Fahrt (`firstClass`, `secondClass`, `freeWifi`), eines für die `JourneyPart` A bis B (`bistro`), `NoticeAssignment` in der Fahrt, mit `JourneyPatternRef` und Von-/Bis-Halt sowie eine auf Frame-Ebene ohne Zuordnung. | gültig |
| `ch20_midnight.xml` | Fahrten über Mitternacht: SYN 1 ab 23:50 ohne `DepartureDayOffset` (Standardwert 0), Tageswechsel während der Fahrt; SYN 2 ab 00:11 mit `DepartureDayOffset` 1. | gültig |
| `ch20_missing_runtime.xml` | Fehlender Summand: keine `JourneyRunTime` für den zweiten `TimingLink`; Ankunft am dritten Halt „nicht berechenbar“. | gültig |
| `ch20_unresolved_ref.xml` | Nicht auflösbare Referenz: dritter Halt verweist auf `ch:1:sloid:SYN9:0:1` (mit `versionRef`, damit nur die Referenzprüfung anschlägt). | gültig |
| `ch20_duplicate_id.xml` | Doppelte ID: `ScheduledStopPoint` `ch:1:sloid:SYN2:0:1` zweimal (mehrdeutig). | ungültig (Schlüssel doppelt), beabsichtigt |
| `ch20_calls.xml` | Fahrt mit `calls/Call`: im CH-Profil 2.0 verboten, verletzt die Kernregel. | gültig (XSD erlaubt `calls`) |
| `ch20_network_offer.xml` | `NETWORK_OFFER` ohne `SiteFrame`; Verweise auf `StopPlace`/`Quay` mit `versionRef` in die Datei `ch20_site_offer.xml`. Allein: `external_or_unloaded`. | gültig |
| `ch20_site_offer.xml` | `SITE_OFFER` nur mit `SiteFrame`: Gegenstück zu `ch20_network_offer.xml` (Referenz über Dateigrenzen). | gültig |
| `broken_xml.xml` | Kein wohlgeformtes XML (`</Nam>` statt `</Name>` in Zeile 48). | nicht lesbar |
| `netex110_like.xml` | Nachbildung des Aufbaus der Lieferung 2027 (NeTEx 1.10): UTF-8-BOM, Kommentar `Profile: SBBSplitted`, `version="1.10"`, `version="any"`, `calls/Call` mit `order`. Muss als 1.10 erkannt und nicht gegen 2.0 geprüft werden. | ungültig gegen 2.1, beabsichtigt |
| `security_xxe.xml` | Sicherheitstest: `DOCTYPE` mit externer Entität auf `xxe_secret.txt`. Muss abgewiesen werden; der Inhalt von `xxe_secret.txt` darf nie erscheinen. lxml stürzt bei der Schema-Prüfung dieser Datei ab („Internal error“), deshalb muss die Datei vor lxml abgewiesen werden. | nicht prüfen |
| `xxe_secret.txt` | Ziel der externen Entität in `security_xxe.xml`. | – |

**Kernregeln:** Ausser `ch20_three_stops.xml` und `ch20_offers.xml` haben die `ch20_*`-Dateien keine `TypeOfProductCategoryRef` und verletzen deshalb die Kernregel CH-SJ-07 (Pflicht); `ch20_calls.xml` zusätzlich CH-SJ-13 (`calls` verboten).

**ZIP mit mehreren Dateien:** ZIP-Dateien sind per `.gitignore` ausgeschlossen. Die Tests erzeugen sie zur Laufzeit aus diesen Dateien (z. B. `ch20_network_offer.xml` + `ch20_site_offer.xml`), ebenso ZIP-Dateien für Zip-Slip und Grenzwerte.

Die XSD-Spalte wurde am 31.10.2026 mit lxml gegen `xsd/xsd/NeTEx_publication.xsd` des Guide-Klons geprüft.

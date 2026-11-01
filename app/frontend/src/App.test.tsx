import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { App } from "./App";
import { ApiError } from "./api";
import {
  APP_INFO,
  DATASET,
  GUIDE,
  JOURNEYS,
  fakeSource as source,
  TARGET_OBJECT,
  VALIDATED_DATASET,
} from "./testData";
import type { DatasetInfo, ExampleInfo, JourneyInfo } from "./types";

/** Wählt ein Beispiel in der Auswahlliste der Kopfzeile. */
async function chooseExample(name: string) {
  fireEvent.change(await screen.findByLabelText("Datensatz"), { target: { value: name } });
}

/** Klappt die Angaben des Guide-Status in der Kopfzeile auf. */
async function openGuideStatus() {
  fireEvent.click(await screen.findByRole("button", { name: /^Guide:/ }));
}

/** Wartet, bis die Fahrtenliste die synthetische Fahrt zeigt, und öffnet sie. */
async function clickJourney() {
  fireEvent.click(await screen.findByRole("button", { name: /Synthetisch A/ }));
}

describe("App", () => {
  it("zeigt in der Kopfzeile den Guide-Status als Punkt mit Kurztext und klappt die Angaben auf", async () => {
    render(<App dataSource={source()} />);
    const status = await screen.findByRole("button", { name: "Guide: ok" });
    expect(status.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByText("Guide-Stand")).toBeNull();
    fireEvent.click(status);
    expect(screen.getByText("Guide-Stand")).toBeTruthy();
    expect(status.getAttribute("aria-expanded")).toBe("true");
  });

  it("zeigt auf der Startseite die Anleitung und die Beispiele, Beispiel 01 hervorgehoben", async () => {
    const guide = {
      ...GUIDE,
      examples: [
        { ...(GUIDE.examples[0] as ExampleInfo), name: "01_einfach.xml", title: "Einfache Fahrt" },
        ...GUIDE.examples,
      ],
    };
    render(<App dataSource={source({ getGuide: () => Promise.resolve(guide) })} />);
    expect(await screen.findByText("So beginnen Sie")).toBeTruthy();
    expect(screen.getByText(/Links eine Fahrt anklicken/)).toBeTruthy();
    expect(screen.getByText("Einfache Fahrt")).toBeTruthy();
    expect(screen.getAllByText("Hier beginnen: einfache Zugfahrt").length).toBe(1);
    expect(screen.queryByRole("tablist")).toBeNull();
  });

  it("öffnet die Hilfe aus der Kopfzeile und kehrt zurück", async () => {
    render(<App dataSource={source()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Hilfe" }));
    expect(screen.getByText("Durchgeführte Prüfungen")).toBeTruthy();
    fireEvent.click(screen.getByText("Zurück"));
    expect(screen.getByText("So beginnen Sie")).toBeTruthy();
  });

  it("schaltet die Sprache um", async () => {
    render(<App dataSource={source()} />);
    await openGuideStatus();
    fireEvent.change(await screen.findByLabelText("Sprache"), { target: { value: "en" } });
    expect(screen.getByText("Guide version")).toBeTruthy();
    expect(document.documentElement.lang).toBe("en");
  });

  it("zeigt Meldungen zu den Einstellungen", async () => {
    const info = {
      ...APP_INFO,
      issues: [
        {
          severity: "warning" as const,
          key: "config.file_missing",
          params: { file: "config/settings.json" },
        },
      ],
    };
    render(<App dataSource={source({ getAppInfo: () => Promise.resolve(info) })} />);
    const status = await screen.findByRole("button", { name: "Guide: Abweichung" });
    expect(screen.queryByText(/config\/settings.json fehlt/)).toBeNull();
    fireEvent.click(status);
    expect(await screen.findByText(/config\/settings.json fehlt/)).toBeTruthy();
  });

  it("zeigt den Fehlerschlüssel der Schnittstelle", async () => {
    render(
      <App
        dataSource={source({ getGuide: () => Promise.reject(new ApiError("error.internal")) })}
      />,
    );
    expect((await screen.findByRole("alert")).textContent).toContain("Interner Fehler");
  });

  it("meldet eine nicht erreichbare Schnittstelle", async () => {
    render(
      <App dataSource={source({ getAppInfo: () => Promise.reject(new TypeError("offline")) })} />,
    );
    expect((await screen.findByRole("alert")).textContent).toContain("antwortet nicht");
  });
});

describe("App mit Datensatz", () => {
  it("öffnet ein Beispiel, zeigt Fahrten und führt über Objekt zur XML-Stelle", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    render(<App dataSource={source({ getObjectXml })} />);
    await chooseExample("ch20_three_stops.xml");
    expect(await screen.findByText("SYN")).toBeTruthy();
    expect(screen.getByText(/ch:1:sloid:SYN9:0:1: nicht in dieser Datei aufgelöst/)).toBeTruthy();
    await clickJourney();
    fireEvent.click(await screen.findByRole("button", { name: "Objekt" }));
    expect(await screen.findByText(/TimetableFrame\/vehicleJourneys/)).toBeTruthy();
    expect(getObjectXml).toHaveBeenCalledWith("SYNTHETICDATASET01.100");
    fireEvent.click(screen.getByRole("button", { name: /DepartureTime/ }));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.104");
  });

  it("zeigt in der Liste Produktkategorie und Zugnummer, den Tag nur bei Verschiebung", async () => {
    const shifted: JourneyInfo = {
      ...(JOURNEYS[0] as JourneyInfo),
      departureDayOffset: { status: "found" as const, text: "1", objectId: "x" },
    };
    const { unmount } = render(<App dataSource={source()} />);
    await chooseExample("ch20_three_stops.xml");
    const item = await screen.findByRole("button", { name: /Synthetisch A/ });
    expect(within(item).getByText("SYN").className).toContain("badge");
    expect(item.textContent).not.toContain("DepartureDayOffset");
    expect(item.textContent).not.toContain("+1");
    unmount();
    render(<App dataSource={source({ getJourneys: () => Promise.resolve([shifted]) })} />);
    await chooseExample("ch20_three_stops.xml");
    expect((await screen.findByRole("button", { name: /Synthetisch A/ })).textContent).toContain(
      "+1",
    );
  });

  it("verwirft die Antwort einer älteren Öffnung", async () => {
    let resolveFirst: (value: DatasetInfo) => void = () => undefined;
    const first = new Promise<DatasetInfo>((resolve) => {
      resolveFirst = resolve;
    });
    const second = { ...DATASET, id: "SYNTHETICDATASET02" };
    const openExample = vi
      .fn<(name: string) => Promise<DatasetInfo>>()
      .mockReturnValueOnce(first)
      .mockResolvedValueOnce(second);
    const getJourneys = vi.fn(source().getJourneys);
    render(<App dataSource={source({ openExample, getJourneys })} />);
    await chooseExample("ch20_three_stops.xml");
    await chooseExample("broken_xml.xml");
    await screen.findByRole("button", { name: /Synthetisch A/ });
    await act(async () => {
      resolveFirst(DATASET);
    });
    expect(getJourneys).toHaveBeenCalledTimes(1);
    expect(getJourneys).toHaveBeenCalledWith("SYNTHETICDATASET02");
  });

  it("zeigt den Status pro Beispiel", async () => {
    render(<App dataSource={source()} />);
    expect(await screen.findByText(/nicht lesbar/)).toBeTruthy();
    expect(screen.getByText("neu")).toBeTruthy();
    expect(screen.getByText("ohne Meldungen")).toBeTruthy();
  });

  it("zeigt ein Beispiel, dessen Prüfung fehlgeschlagen ist", async () => {
    const failed = {
      ...GUIDE,
      examples: GUIDE.examples.map((example, index) =>
        index === 0 ? { ...example, result: "check_failed" as const } : example,
      ),
    };
    render(<App dataSource={source({ getGuide: () => Promise.resolve(failed) })} />);
    expect(await screen.findByText(/Prüfung fehlgeschlagen/)).toBeTruthy();
  });

  it("meldet einen Fehler beim Öffnen", async () => {
    render(
      <App
        dataSource={source({ openExample: () => Promise.reject(new ApiError("error.not_found")) })}
      />,
    );
    await chooseExample("ch20_three_stops.xml");
    expect((await screen.findByRole("alert")).textContent).toContain("Nicht gefunden");
  });
});

describe("App mit Referenzen und Herkunft", () => {
  async function openJourney(overrides = {}) {
    render(<App dataSource={source(overrides)} />);
    await chooseExample("ch20_three_stops.xml");
    await clickJourney();
    fireEvent.click(await screen.findByRole("button", { name: "Objekt" }));
    await screen.findByText("Verweist auf");
  }

  it("zeigt ausgehende Verweise mit Status und Ziel", async () => {
    await openJourney();
    expect(screen.getAllByText("aufgelöst").length).toBeGreaterThan(0);
    expect(screen.getByText("nicht auflösbar")).toBeTruthy();
    expect(screen.getByText("erwartet: Line")).toBeTruthy();
    expect(screen.getByText("keine Verweise")).toBeTruthy();
  });

  it("folgt einem Verweis zum Ziel, zeigt eingehende Verweise und geht zurück und vor", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    await openJourney({ getObjectXml });
    fireEvent.click(
      screen.getAllByRole("button", { name: /^Operator ch:1:sboid/ })[0] as HTMLElement,
    );
    expect(await screen.findByText("Wird verwiesen von")).toBeTruthy();
    expect(getObjectXml).toHaveBeenLastCalledWith(TARGET_OBJECT.id);
    expect(screen.getByRole("button", { name: /Vor im Verlauf/ }).hasAttribute("disabled")).toBe(
      true,
    );
    fireEvent.click(screen.getByRole("button", { name: /Zurück im Verlauf/ }));
    expect(await screen.findByText("Verweist auf")).toBeTruthy();
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.100");
    fireEvent.click(screen.getByRole("button", { name: /Vor im Verlauf/ }));
    expect(getObjectXml).toHaveBeenLastCalledWith(TARGET_OBJECT.id);
  });

  it("springt aus der Eigenschaft zum Ziel des Verweises", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    await openJourney({ getObjectXml });
    fireEvent.click(screen.getByRole("button", { name: /Zum Ziel/ }));
    expect(getObjectXml).toHaveBeenLastCalledWith(TARGET_OBJECT.id);
  });

  it("zeigt die Herkunftskette und markiert das gewählte Glied", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    await openJourney({ getObjectXml });
    const frame = await screen.findByRole("button", { name: /^TimetableFrame/ });
    fireEvent.click(frame);
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.90");
  });

  it("blendet die Herkunftskette aus, solange die Stelle einer Diagnose gezeigt wird", async () => {
    const diagnostic = {
      category: "reference",
      severity: "info" as const,
      key: "reference.external_or_unloaded",
      params: { element: "FromPointRef", ref: "x", expected: "ScheduledStopPoint" },
      fileId: 1,
      fileName: "ch20_three_stops.xml",
      line: 53,
      column: 8,
    };
    await openJourney({ getDiagnostics: () => Promise.resolve([diagnostic]) });
    expect(screen.getAllByRole("button", { name: /^TimetableFrame/ }).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("tab", { name: "Prüfung" }));
    fireEvent.click(await screen.findByRole("button", { name: /Zeile 53/ }));
    expect(await screen.findByText("Eine Angabe wählen, um ihre Herkunft zu sehen.")).toBeTruthy();
  });
});

describe("rechte Spalte", () => {
  it("erscheint erst bei einer Auswahl, zeigt die Legende und lässt sich schliessen", async () => {
    render(<App dataSource={source()} />);
    await chooseExample("ch20_three_stops.xml");
    await clickJourney();
    await screen.findByRole("region", { name: "Halte und Zeiten" });
    // Die Fahrt aus der Liste zu öffnen wählt noch keine Angabe: nur der Hauptbereich.
    expect(screen.queryByRole("complementary", { name: "Herkunft und XML" })).toBeNull();
    const table = document.querySelector(".stop-table") as HTMLElement;
    fireEvent.click(within(table).getByText("Synthetisch A"));
    const column = await screen.findByRole("complementary", { name: "Herkunft und XML" });
    expect(within(column).getByText("Frame-Farben")).toBeTruthy();
    expect(document.querySelector(".layout-details")).not.toBeNull();
    fireEvent.click(within(column).getByRole("button", { name: "Schliessen" }));
    expect(screen.queryByRole("complementary", { name: "Herkunft und XML" })).toBeNull();
    expect(document.querySelector(".layout-details")).toBeNull();
    expect(screen.getByRole("region", { name: "Halte und Zeiten" })).toBeTruthy();
  });

  it("verweist aus der Legende auf die Hilfe", async () => {
    render(<App dataSource={source()} />);
    await chooseExample("ch20_three_stops.xml");
    await clickJourney();
    await screen.findByRole("region", { name: "Halte und Zeiten" });
    const table = document.querySelector(".stop-table") as HTMLElement;
    fireEvent.click(within(table).getByText("Synthetisch A"));
    fireEvent.click(await screen.findByText("Was bedeuten die Farben?"));
    expect(screen.getByText("Durchgeführte Prüfungen")).toBeTruthy();
  });

  it("zeigt den Reiter Prüfung mit der Anzahl der Befunde erst nach dem Prüfen", async () => {
    render(<App dataSource={source({ openExample: () => Promise.resolve(VALIDATED_DATASET) })} />);
    await chooseExample("ch20_three_stops.xml");
    expect(await screen.findByRole("tab", { name: "Prüfung (1)" })).toBeTruthy();
  });
});

describe("App mit Fahrtansicht", () => {
  async function openJourneyView(overrides = {}) {
    render(<App dataSource={source(overrides)} />);
    await chooseExample("ch20_three_stops.xml");
    await clickJourney();
    await screen.findByRole("region", { name: "Halte und Zeiten" });
  }

  it("öffnet die Fahrt als Fahrplananzeige mit Kopf, Zeiten und Symbol für berechnete Zeiten", async () => {
    await openJourneyView();
    expect(screen.getByRole("button", { name: "Fahrt" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getAllByText("Synthetisch A").length).toBeGreaterThan(0);
    // Uneingeschränktes Ein- und Aussteigen steht nicht in Worten; nur Einschränkungen.
    expect(screen.getByText("nur Einsteigen")).toBeTruthy();
    expect(screen.getByText("nur Aussteigen")).toBeTruthy();
    expect(screen.queryByText("Ein- und Aussteigen")).toBeNull();
    expect(screen.getAllByRole("img", { name: "berechnet" }).length).toBe(2);
    expect(screen.getAllByText("08:00").length).toBeGreaterThan(0);
    // Ankunft und Abfahrt am zweiten Halt, dazu das Ende der Teilstrecke.
    expect(screen.getAllByText("08:10").length).toBe(3);
    expect(screen.getByText("Gültig 13.12.2026 bis 19.12.2026")).toBeTruthy();
    expect(screen.getByText(/5 Betriebstage \(7 Tage im Zeitraum\)/)).toBeTruthy();
    // Ohne „Herkunft zeigen“ keine Zusatzzeilen; mit dem Schalter erscheinen sie.
    expect(screen.queryByText("ForBoarding")).toBeNull();
    fireEvent.click(screen.getByRole("checkbox", { name: "Herkunft zeigen" }));
    expect(screen.getAllByText("ForBoarding").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Haltestelle (StopPlace)").length).toBe(3);
  });

  it("zeigt „nicht berechenbar“ mit Grund statt einer Uhrzeit", async () => {
    await openJourneyView();
    expect(screen.getByText("nicht berechenbar")).toBeTruthy();
    expect(
      screen.getAllByText(/Im TimeDemandType fehlt für den TimingLink tl-2 eine JourneyRunTime/)
        .length,
    ).toBeGreaterThan(0);
  });

  it("zeigt Teilstrecke, Angebot mit Stammdaten und Hinweis in allen Sprachen", async () => {
    await openJourneyView();
    expect(screen.getByText("Teilstrecken")).toBeTruthy();
    expect(screen.getAllByText("bistro").length).toBeGreaterThan(0);
    expect(screen.getAllByText("WS · Bistro").length).toBeGreaterThan(0);
    expect(screen.getByText("Synthetischer Hinweis")).toBeTruthy();
    expect(screen.getByText("Synthetic notice")).toBeTruthy();
  });

  it("zeigt die Rechenkette einer Zeit und markiert den Summanden im XML", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    await openJourneyView({ getObjectXml });
    const arrival = screen.getAllByText("08:10")[0] as HTMLElement;
    fireEvent.click(arrival);
    expect(await screen.findByText("Rechenkette")).toBeTruthy();
    expect(screen.getByText(/Ankunft an Halt 2 \(Synthetisch B\):/)).toBeTruthy();
    expect(screen.getByText("Abfahrt am ersten Halt (DepartureTime)")).toBeTruthy();
    expect(screen.getByText("+ Fahrzeit (RunTime)")).toBeTruthy();
    expect(
      screen.getByText("TimingLink über FromPointRef/ToPointRef bestimmt", { exact: false }),
    ).toBeTruthy();
    // Die Quelle der Zeit ist der letzte Summand (RunTime).
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.130");
    const chain = screen.getByRole("region", { name: "Rechenkette" });
    fireEvent.click(within(chain).getByText("08:00:00"));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.104");
    expect(screen.getByText("Rechenkette")).toBeTruthy();
  });

  it("kennzeichnet Standardwerte der Rechenkette", async () => {
    await openJourneyView();
    const departure = screen.getAllByText("08:10")[1] as HTMLElement;
    fireEvent.click(departure);
    expect(
      await screen.findByText(/Standardwert 0: keine JourneyWaitTime für diesen Halt/),
    ).toBeTruthy();
  });

  it("zeigt bei nicht berechenbarer Zeit den Grund in der Rechenkette", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    await openJourneyView({ getObjectXml });
    fireEvent.click(screen.getByText("nicht berechenbar"));
    expect(await screen.findByText(/Ankunft an Halt 3/)).toBeTruthy();
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.121");
  });

  it("wählt einen Halt und zeigt seine Herkunft", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    await openJourneyView({ getObjectXml });
    const table = document.querySelector(".stop-table") as HTMLElement;
    fireEvent.click(within(table).getByText("Synthetisch A"));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.211");
    // Die Rechenkette gehört zu einer Zeit und verschwindet mit der Auswahl eines Halts.
    expect(screen.queryByText("Rechenkette")).toBeNull();
  });

  it("schaltet zwischen Fahrt und Objekt um und merkt sich die Ansicht im Verlauf", async () => {
    await openJourneyView();
    fireEvent.click(screen.getByRole("button", { name: "Objekt" }));
    expect(await screen.findByText("Verweist auf")).toBeTruthy();
    expect(screen.queryByRole("region", { name: "Halte und Zeiten" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Zurück im Verlauf/ }));
    expect(await screen.findByRole("region", { name: "Halte und Zeiten" })).toBeTruthy();
  });

  it("zeigt die Diagnosen der Fahrt mit Stelle", async () => {
    const getXmlAt = vi.fn(source().getXmlAt);
    await openJourneyView({ getXmlAt });
    fireEvent.click(await screen.findByRole("button", { name: /Zeile 121/ }));
    expect(getXmlAt).toHaveBeenCalledWith("SYNTHETICDATASET01", 1, 121, 8);
  });

  it("meldet einen Fehler der Fahrtansicht", async () => {
    await openJourneyView({
      getJourney: () => Promise.reject(new ApiError("error.not_found")),
    }).catch(() => undefined);
    expect((await screen.findByRole("alert")).textContent).toContain("Nicht gefunden");
  });
});

describe("App mit eigenen Dateien und Prüfung", () => {
  const files = [new File(["<a/>"], "eigene.xml")];

  async function chooseFiles(dataSource = source(), openCheck = true) {
    render(<App dataSource={dataSource} />);
    const input = (await screen.findByLabelText("Dateien auswählen")) as HTMLInputElement;
    fireEvent.change(input, { target: { files } });
    if (openCheck) {
      fireEvent.click(await screen.findByRole("tab", { name: "Prüfung" }));
    }
  }

  it("öffnet eigene Dateien über den Dialog und zeigt die Versionserkennung", async () => {
    const openFiles = vi.fn(source().openFiles);
    await chooseFiles(source({ openFiles }));
    expect(await screen.findByText("Erkannt: CH-Profil 2.0 (Entwurf)")).toBeTruthy();
    expect(openFiles).toHaveBeenCalledWith(files);
    fireEvent.click(screen.getByRole("tab", { name: "Fahrten" }));
    expect(await screen.findByRole("button", { name: /Synthetisch A/ })).toBeTruthy();
  });

  it("startet die Prüfung und lädt die Diagnosen neu", async () => {
    const getDiagnostics = vi
      .fn<ReturnType<typeof source>["getDiagnostics"]>()
      .mockResolvedValueOnce([])
      .mockResolvedValue([
        {
          category: "profile_rule",
          severity: "error",
          key: "core.forbidden_present",
          params: {
            rule: "CH-SJ-13",
            element: "ServiceJourney",
            id: "ch:1:sjyid:SYN:1",
            path: "calls",
            source: "templates/ServiceJourney.xml Z. 145-153",
          },
          fileId: 1,
          fileName: "ch20_calls.xml",
          line: 164,
          column: 8,
          guideLink:
            "https://github.com/openTdataCH/netexRealisationGuideSwitzerland/blob/b7ac158/src/02_files.md",
        },
      ]);
    const validate = vi.fn(() => Promise.resolve(VALIDATED_DATASET));
    await chooseFiles(source({ getDiagnostics, validate }));
    fireEvent.click(await screen.findByRole("button", { name: "Prüfen" }));
    expect(await screen.findByText("Geprüft gegen Entwurf b7ac158")).toBeTruthy();
    expect(validate).toHaveBeenCalledWith(DATASET.id, false);
    expect(
      await screen.findByText(/CH-SJ-13: ServiceJourney ch:1:sjyid:SYN:1 darf calls/),
    ).toBeTruthy();
    const link = screen.getByRole("link", { name: "Guide-Kapitel" });
    expect(link.getAttribute("href")).toContain("/blob/b7ac158/src/02_files.md");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(screen.getByRole("heading", { name: "Profilregel" })).toBeTruthy();
  });

  it("wendet das Ergebnis einer Prüfung nicht auf einen später geöffneten Datensatz an", async () => {
    let resolveValidation: (value: DatasetInfo) => void = () => undefined;
    const validate = vi.fn(
      () =>
        new Promise<DatasetInfo>((resolve) => {
          resolveValidation = resolve;
        }),
    );
    const second = { ...DATASET, id: "SYNTHETICDATASET02" };
    const openFiles = vi
      .fn<(files: File[]) => Promise<DatasetInfo>>()
      .mockResolvedValueOnce(DATASET)
      .mockResolvedValue(second);
    await chooseFiles(source({ validate, openFiles }));
    fireEvent.click(await screen.findByRole("button", { name: "Prüfen" }));
    expect(await screen.findByText("Prüfung läuft …")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Dateien auswählen"), { target: { files } });
    await vi.waitFor(() => expect(openFiles).toHaveBeenCalledTimes(2));
    fireEvent.click(await screen.findByRole("tab", { name: "Prüfung" }));
    expect(await screen.findByText("Noch nicht geprüft.")).toBeTruthy();
    await act(async () => {
      resolveValidation(VALIDATED_DATASET);
    });
    expect(screen.getByText("Noch nicht geprüft.")).toBeTruthy();
    expect(screen.queryByText("Geprüft gegen Entwurf b7ac158")).toBeNull();
    expect(screen.queryByText("Prüfung läuft …")).toBeNull();
  });

  it("zeigt den Fehler einer Prüfung nicht bei einem später geöffneten Datensatz", async () => {
    let rejectValidation: (reason: unknown) => void = () => undefined;
    const validate = vi.fn(
      () =>
        new Promise<DatasetInfo>((_resolve, reject) => {
          rejectValidation = reject;
        }),
    );
    const openFiles = vi
      .fn<(files: File[]) => Promise<DatasetInfo>>()
      .mockResolvedValueOnce(DATASET)
      .mockResolvedValue({ ...DATASET, id: "SYNTHETICDATASET02" });
    await chooseFiles(source({ validate, openFiles }));
    fireEvent.click(await screen.findByRole("button", { name: "Prüfen" }));
    fireEvent.change(screen.getByLabelText("Dateien auswählen"), { target: { files } });
    await vi.waitFor(() => expect(openFiles).toHaveBeenCalledTimes(2));
    fireEvent.click(await screen.findByRole("tab", { name: "Prüfung" }));
    await act(async () => {
      rejectValidation(new ApiError("error.internal"));
    });
    expect(screen.queryByText(/Interner Fehler/)).toBeNull();
    expect(screen.getByRole("button", { name: "Prüfen" })).toBeTruthy();
  });

  it("lädt die Diagnosen bei jeder erneuten Prüfung neu", async () => {
    const getDiagnostics = vi.fn<ReturnType<typeof source>["getDiagnostics"]>(() =>
      Promise.resolve([]),
    );
    await chooseFiles(source({ getDiagnostics }));
    const button = await screen.findByRole("button", { name: "Prüfen" });
    await vi.waitFor(() => expect(getDiagnostics).toHaveBeenCalledTimes(1));
    fireEvent.click(button);
    await vi.waitFor(() => expect(getDiagnostics).toHaveBeenCalledTimes(2));
    fireEvent.click(await screen.findByRole("button", { name: "Prüfen" }));
    await vi.waitFor(() => expect(getDiagnostics).toHaveBeenCalledTimes(3));
  });

  it("meldet einen Fehler der Prüfung", async () => {
    const validate = () => Promise.reject(new ApiError("error.internal"));
    await chooseFiles(source({ validate }));
    fireEvent.click(await screen.findByRole("button", { name: "Prüfen" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Interner Fehler");
  });

  it("schliesst den bisherigen Datensatz beim Öffnen eines neuen", async () => {
    const closeDataset = vi.fn(() => Promise.resolve());
    const openFiles = vi.fn(() => Promise.resolve({ ...DATASET, id: "SYNTHETICDATASET02" }));
    render(<App dataSource={source({ closeDataset, openFiles })} />);
    await chooseExample("ch20_three_stops.xml");
    await screen.findByRole("button", { name: /Synthetisch A/ });
    fireEvent.change(screen.getByLabelText("Dateien auswählen"), { target: { files } });
    await vi.waitFor(() => expect(openFiles).toHaveBeenCalled());
    expect(closeDataset).toHaveBeenCalledWith(DATASET.id);
  });

  it("schliesst einen Datensatz, dessen Öffnung überholt wurde", async () => {
    let resolveFirst: (value: DatasetInfo) => void = () => undefined;
    const first = new Promise<DatasetInfo>((resolve) => {
      resolveFirst = resolve;
    });
    const closeDataset = vi.fn(() => Promise.resolve());
    const openExample = vi
      .fn<(name: string) => Promise<DatasetInfo>>()
      .mockReturnValueOnce(first)
      .mockResolvedValue({ ...DATASET, id: "SYNTHETICDATASET02" });
    render(<App dataSource={source({ openExample, closeDataset })} />);
    await chooseExample("ch20_three_stops.xml");
    await chooseExample("broken_xml.xml");
    await screen.findByRole("button", { name: /Synthetisch A/ });
    await act(async () => {
      resolveFirst({ ...DATASET, id: "SYNTHETICDATASET01" });
    });
    expect(closeDataset).toHaveBeenCalledWith("SYNTHETICDATASET01");
  });

  it("meldet einen Fehler beim Öffnen eigener Dateien", async () => {
    const openFiles = () => Promise.reject(new ApiError("error.payload_too_large"));
    await chooseFiles(source({ openFiles }), false);
    expect((await screen.findByRole("alert")).textContent).toContain("grösser als erlaubt");
  });
});

describe("App während die XSD geladen wird", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("fragt den Guide-Stand nach, bis die Beispiele geprüft sind", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const pending = {
      ...GUIDE,
      examplesReady: false,
      xsdLoaded: false,
      examples: GUIDE.examples.map((example) => ({ ...example, result: null })),
    };
    const getGuide = vi.fn().mockResolvedValueOnce(pending).mockResolvedValue(GUIDE);
    render(<App dataSource={source({ getGuide })} />);
    await openGuideStatus();
    expect(await screen.findByText("XSD wird geladen …")).toBeTruthy();
    expect(screen.getAllByText(/wird geprüft …/).length).toBe(2);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });
    expect(await screen.findByText("bereit")).toBeTruthy();
    expect(screen.getByText("ohne Meldungen")).toBeTruthy();
    expect(getGuide).toHaveBeenCalledTimes(2);
  });

  it("zeigt einen Fehler der Nachfrage erst nach mehreren Fehlschlägen in Folge", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const pending = { ...GUIDE, examplesReady: false, xsdLoaded: false };
    const getGuide = vi
      .fn()
      .mockResolvedValueOnce(pending)
      .mockRejectedValue(new ApiError("error.internal"));
    render(<App dataSource={source({ getGuide })} />);
    await openGuideStatus();
    await screen.findByText("XSD wird geladen …");
    for (let attempt = 1; attempt < 5; attempt += 1) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2100);
      });
      expect(screen.queryByRole("alert")).toBeNull();
    }
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });
    expect((await screen.findByRole("alert")).textContent).toContain("Interner Fehler");
    expect(getGuide).toHaveBeenCalledTimes(6);
  });

  it("fragt nach einem einzelnen Fehler weiter nach", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const pending = { ...GUIDE, examplesReady: false, xsdLoaded: false };
    const getGuide = vi
      .fn()
      .mockResolvedValueOnce(pending)
      .mockRejectedValueOnce(new ApiError("error.internal"))
      .mockResolvedValue(GUIDE);
    render(<App dataSource={source({ getGuide })} />);
    await openGuideStatus();
    await screen.findByText("XSD wird geladen …");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });
    expect(screen.queryByRole("alert")).toBeNull();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });
    expect(await screen.findByText("bereit")).toBeTruthy();
    expect(getGuide).toHaveBeenCalledTimes(3);
  });
});

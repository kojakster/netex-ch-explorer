import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { App } from "./App";
import { ApiError } from "./api";
import { APP_INFO, DATASET, fakeSource as source, TARGET_OBJECT } from "./testData";
import type { DatasetInfo } from "./types";

describe("App", () => {
  it("zeigt nach dem Laden Guide-Status und Legende", async () => {
    render(<App dataSource={source()} />);
    expect(await screen.findByText("Guide-Stand")).toBeTruthy();
    expect(screen.getByText("Frame-Farben")).toBeTruthy();
  });

  it("öffnet die Hilfe aus der Legende und kehrt zurück", async () => {
    render(<App dataSource={source()} />);
    fireEvent.click(await screen.findByText("Was bedeuten die Farben?"));
    expect(screen.getByText("Durchgeführte Prüfungen")).toBeTruthy();
    fireEvent.click(screen.getByText("Zurück"));
    expect(screen.getByText("Guide-Stand")).toBeTruthy();
  });

  it("schaltet die Sprache um", async () => {
    render(<App dataSource={source()} />);
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
    fireEvent.click(await screen.findByText("ch20_three_stops.xml"));
    expect(await screen.findByText("Synthetische Linie")).toBeTruthy();
    expect(screen.getByText(/ch:1:sloid:SYN9:0:1: nicht in dieser Datei aufgelöst/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "ServiceJourney" }));
    fireEvent.click(await screen.findByRole("button", { name: "Objekt" }));
    expect(await screen.findByText(/TimetableFrame\/vehicleJourneys/)).toBeTruthy();
    expect(getObjectXml).toHaveBeenCalledWith("SYNTHETICDATASET01.100");
    fireEvent.click(screen.getByRole("button", { name: /DepartureTime/ }));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.104");
  });

  it("zeigt Zugnummer und DepartureDayOffset mit Herkunft", async () => {
    const getObjectXml = vi.fn(source().getObjectXml);
    render(<App dataSource={source({ getObjectXml })} />);
    fireEvent.click(await screen.findByText("ch20_three_stops.xml"));
    fireEvent.click(await screen.findByRole("button", { name: "(DepartureDayOffset 0)" }));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.105");
    fireEvent.click(screen.getByRole("button", { name: "1" }));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.110");
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
    fireEvent.click(await screen.findByText("ch20_three_stops.xml"));
    fireEvent.click(screen.getByText("broken_xml.xml"));
    await screen.findByText("Synthetische Linie");
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

  it("meldet einen Fehler beim Öffnen", async () => {
    render(
      <App
        dataSource={source({ openExample: () => Promise.reject(new ApiError("error.not_found")) })}
      />,
    );
    fireEvent.click(await screen.findByText("ch20_three_stops.xml"));
    expect((await screen.findByRole("alert")).textContent).toContain("Nicht gefunden");
  });
});

describe("App mit Referenzen und Herkunft", () => {
  async function openJourney(overrides = {}) {
    render(<App dataSource={source(overrides)} />);
    fireEvent.click(await screen.findByText("ch20_three_stops.xml"));
    fireEvent.click(await screen.findByRole("button", { name: "ServiceJourney" }));
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
    fireEvent.click(await screen.findByRole("button", { name: /Zeile 53/ }));
    expect(await screen.findByText("Eine Angabe wählen, um ihre Herkunft zu sehen.")).toBeTruthy();
  });
});

describe("App mit Fahrtansicht", () => {
  async function openJourneyView(overrides = {}) {
    render(<App dataSource={source(overrides)} />);
    fireEvent.click(await screen.findByText("ch20_three_stops.xml"));
    fireEvent.click(await screen.findByRole("button", { name: "ServiceJourney" }));
    await screen.findByText("Halte und Zeiten");
  }

  it("öffnet die Fahrt als Fahrplan mit Kopf, Zeiten und Markierung „berechnet“", async () => {
    await openJourneyView();
    expect(screen.getByRole("button", { name: "Fahrt" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getAllByText("Synthetisch A").length).toBeGreaterThan(0);
    expect(screen.getByText("nur Einsteigen")).toBeTruthy();
    expect(screen.getAllByText("Ein- und Aussteigen").length).toBeGreaterThan(0);
    expect(screen.getByText("nur Aussteigen")).toBeTruthy();
    expect(screen.getAllByText("berechnet").length).toBe(2);
    expect(screen.getAllByText("08:00").length).toBeGreaterThan(0);
    // Ankunft und Abfahrt am zweiten Halt, dazu das Ende der Teilstrecke.
    expect(screen.getAllByText("08:10").length).toBe(3);
    expect(screen.getByText("14.12.2026")).toBeTruthy();
    expect(screen.getByText(/7 Tage im Zeitraum, 5 Betriebstage/)).toBeTruthy();
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
    expect(screen.getByText("Teilstrecken (JourneyPart)")).toBeTruthy();
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
    expect(screen.queryByText("Halte und Zeiten")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Zurück im Verlauf/ }));
    expect(await screen.findByText("Halte und Zeiten")).toBeTruthy();
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

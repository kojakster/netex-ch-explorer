import { fireEvent, render, screen } from "@testing-library/react";
import { App } from "./App";
import { ApiError } from "./api";
import { APP_INFO, fakeSource as source } from "./testData";

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
    fireEvent.click(screen.getAllByText("1")[0] as HTMLElement);
    expect(await screen.findByText(/TimetableFrame\/vehicleJourneys/)).toBeTruthy();
    expect(getObjectXml).toHaveBeenCalledWith("SYNTHETICDATASET01.100");
    fireEvent.click(screen.getByRole("button", { name: /DepartureTime/ }));
    expect(getObjectXml).toHaveBeenLastCalledWith("SYNTHETICDATASET01.104");
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

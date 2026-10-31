import { fireEvent, render, screen } from "@testing-library/react";
import { App } from "./App";
import { ApiError, type DataSource } from "./api";
import { APP_INFO, GUIDE } from "./testData";

function source(overrides: Partial<DataSource> = {}): DataSource {
  return {
    getAppInfo: () => Promise.resolve(APP_INFO),
    getGuide: () => Promise.resolve(GUIDE),
    ...overrides,
  };
}

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

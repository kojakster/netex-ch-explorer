import { fireEvent, render, screen, within } from "@testing-library/react";
import { APP_INFO, GUIDE } from "../testData";
import { HelpPage } from "./HelpPage";

describe("HelpPage", () => {
  it("zeigt Farben und Grau-Liste aus den Daten", () => {
    render(<HelpPage appInfo={APP_INFO} guide={GUIDE} onBack={() => undefined} />);
    expect(screen.getByText("TimetableFrame")).toBeTruthy();
    expect(screen.getByText("#0057B8")).toBeTruthy();
    expect(screen.getByText("für den Fahrplan nicht relevant")).toBeTruthy();
    expect(screen.getByText("SiteFacilitySet")).toBeTruthy();
  });

  it("trennt durchgeführte und nicht durchgeführte Prüfungen", () => {
    render(<HelpPage appInfo={APP_INFO} guide={GUIDE} onBack={() => undefined} />);
    const performed = screen.getByText("Durchgeführte Prüfungen").nextElementSibling;
    const notPerformed = screen.getByText("Nicht durchgeführte Prüfungen").nextElementSibling;
    expect(performed).not.toBeNull();
    expect(notPerformed).not.toBeNull();
    expect(within(performed as HTMLElement).getByText("XSD-Prüfung")).toBeTruthy();
    expect(
      within(notPerformed as HTMLElement).getByText("Übrige Schweizer Profilregeln"),
    ).toBeTruthy();
    expect(within(notPerformed as HTMLElement).queryByText("XSD-Prüfung")).toBeNull();
  });

  it("zeigt alle Schweregrade mit Symbol", () => {
    render(<HelpPage appInfo={APP_INFO} guide={GUIDE} onBack={() => undefined} />);
    for (const symbol of ["⚠", "△", "ℹ"]) {
      expect(screen.getByText(symbol)).toBeTruthy();
    }
  });

  it("zeigt «keine», wenn keine Prüfung durchgeführt wird", () => {
    render(
      <HelpPage
        appInfo={{ ...APP_INFO, checks: [{ id: "xsd", status: "not_implemented", sources: [] }] }}
        guide={null}
        onBack={() => undefined}
      />,
    );
    expect(screen.getByText("keine")).toBeTruthy();
  });

  it("ruft beim Zurück-Knopf onBack auf", () => {
    const onBack = vi.fn();
    render(<HelpPage appInfo={APP_INFO} guide={GUIDE} onBack={onBack} />);
    fireEvent.click(screen.getByText("Zurück"));
    expect(onBack).toHaveBeenCalledOnce();
  });
});

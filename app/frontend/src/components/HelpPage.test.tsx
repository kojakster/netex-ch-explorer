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
      expect(screen.getAllByText(symbol).length).toBeGreaterThan(0);
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

  it("listet die Kernregeln mit Kennung, Schweregrad, Wortlaut und Quelle", () => {
    render(<HelpPage appInfo={APP_INFO} guide={GUIDE} onBack={() => undefined} />);
    const rules = screen.getByText("Schweizer Kernregeln für den Fahrplan").closest("section");
    expect(rules).not.toBeNull();
    const section = within(rules as HTMLElement);
    expect(section.getByText(/CH-SJ-13/)).toBeTruthy();
    expect(section.getByText(/ServiceJourney darf calls nicht enthalten\./)).toBeTruthy();
    expect(
      section.getByText(
        /ServiceAlteration in ServiceJourney muss einen dieser Werte haben: planned\./,
      ),
    ).toBeTruthy();
    expect(section.getByText("templates/ServiceJourney.xml Z. 145-153")).toBeTruthy();
    expect(section.queryByText(/CH-SJP-08/)).toBeNull();
  });

  it("zeigt jede Frame-Farbe und jede Grau-Element der Daten, nicht mehr und nicht weniger", () => {
    const appInfo = {
      ...APP_INFO,
      frameColors: [
        { key: "TimetableFrame", background: "#123456", text: "#FFFFFF" },
        { key: "frame-neu", background: "#654321", text: "#000000" },
      ],
      notRelevantElements: ["NeuesElement"],
    };
    render(<HelpPage appInfo={appInfo} guide={GUIDE} onBack={() => undefined} />);
    expect(screen.getByText("#123456")).toBeTruthy();
    expect(screen.getByText("#654321")).toBeTruthy();
    expect(screen.queryByText("#0057B8")).toBeNull();
    expect(screen.getByText("NeuesElement")).toBeTruthy();
    expect(screen.queryByText("SiteFacilitySet")).toBeNull();
  });

  it("ordnet jede Prüfung der Daten genau einer der beiden Listen zu und nennt Quellen", () => {
    const appInfo = {
      ...APP_INFO,
      checks: [
        { id: "xsd", status: "performed" as const, sources: ["xsd/xsd/NeTEx_publication.xsd"] },
        { id: "ch_profile_rules", status: "deferred" as const, sources: ["src/templates"] },
        { id: "references", status: "not_implemented" as const, sources: [] },
      ],
    };
    render(<HelpPage appInfo={appInfo} guide={GUIDE} onBack={() => undefined} />);
    const performed = screen.getByText("Durchgeführte Prüfungen").nextElementSibling as HTMLElement;
    const notPerformed = screen.getByText("Nicht durchgeführte Prüfungen")
      .nextElementSibling as HTMLElement;
    expect(within(performed).getByText("XSD-Prüfung")).toBeTruthy();
    expect(within(performed).getByText("xsd/xsd/NeTEx_publication.xsd")).toBeTruthy();
    expect(within(performed).queryByText("Referenzen")).toBeNull();
    expect(within(notPerformed).getByText("Übrige Schweizer Profilregeln")).toBeTruthy();
    expect(within(notPerformed).getByText("Referenzen")).toBeTruthy();
    expect(within(notPerformed).getByText("src/templates")).toBeTruthy();
    expect(
      within(notPerformed).getByText(/später \(nicht in der ersten Ausbaustufe\)/),
    ).toBeTruthy();
    expect(
      within(notPerformed).getByText(/noch nicht umgesetzt \(geplant in der ersten Ausbaustufe\)/),
    ).toBeTruthy();
  });

  it("zeigt den Guide-Stand mit Branch, Commit, XSD und Teststand", () => {
    render(<HelpPage appInfo={APP_INFO} guide={GUIDE} onBack={() => undefined} />);
    const guide = screen.getByText("Guide-Stand", { selector: "h2" }).closest("section");
    const section = within(guide as HTMLElement);
    expect(section.getByText("next")).toBeTruthy();
    expect(section.getByText("b7ac158")).toBeTruthy();
    expect(section.getByText("73b337e")).toBeTruthy();
    expect(section.getByText("mit diesem Stand getestet")).toBeTruthy();
  });

  it("zeigt bei fehlender XSD keinen Commit der XSD", () => {
    const guide = { ...GUIDE, xsdPresent: false, xsdLoaded: false };
    render(<HelpPage appInfo={APP_INFO} guide={guide} onBack={() => undefined} />);
    expect(screen.queryByText("73b337e")).toBeNull();
    expect(screen.getByText("fehlt")).toBeTruthy();
  });

  it("zeigt ohne gefundenen Guide keinen Stand", () => {
    render(
      <HelpPage appInfo={APP_INFO} guide={{ ...GUIDE, found: false }} onBack={() => undefined} />,
    );
    expect(screen.queryByText("b7ac158")).toBeNull();
  });
});

import { fireEvent, render, screen, within } from "@testing-library/react";
import { JOURNEY_VIEW } from "../testData";
import type { JourneyViewInfo } from "../types";
import { StructureOverview } from "./StructureOverview";

const COLORS = [
  { key: "ServiceFrame", background: "#1B8A2F", text: "#000000" },
  { key: "TimetableFrame", background: "#0057B8", text: "#FFFFFF" },
];

function renderOverview(journey: JourneyViewInfo = JOURNEY_VIEW, selected: string | null = null) {
  const onSelect = vi.fn();
  render(
    <StructureOverview journey={journey} colors={COLORS} selected={selected} onSelect={onSelect} />,
  );
  return onSelect;
}

describe("StructureOverview", () => {
  it("ist eingeklappt und trägt die Frage als Überschrift", () => {
    renderOverview();
    const details = screen.getByText("Wie ist diese Fahrt aufgebaut?").closest("details");
    expect((details as HTMLDetailsElement).open).toBe(false);
  });

  it("zeigt je Zeile Boxen, den Erklärsatz und die Legende der Frame-Farben", () => {
    renderOverview();
    const stops = screen.getByRole("region", { name: "Halte, Gleise und Haltestellen" });
    expect(within(stops).getByText("ServiceJourneyPattern")).toBeTruthy();
    expect(within(stops).getByText("PassengerStopAssignment")).toBeTruthy();
    expect(within(stops).getByText(/Die Halte kommen aus dem Fahrtmuster/)).toBeTruthy();
    expect(screen.getByRole("region", { name: "Zeiten" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Betriebstage" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Frame-Farben" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Was bedeuten die Farben?" })).toBeNull();
  });

  it("färbt eine Box in der Farbe ihres Frames, nennt den Frame und öffnet beim Klick die Stelle", () => {
    const onSelect = renderOverview();
    const stops = screen.getByRole("region", { name: "Halte, Gleise und Haltestellen" });
    const box = within(stops).getByText("ScheduledStopPoint").closest("button") as HTMLElement;
    expect(box.style.backgroundColor).toBe("rgb(27, 138, 47)");
    expect(within(box).getByText("ServiceFrame")).toBeTruthy();
    expect(within(box).getByText("3×")).toBeTruthy();
    fireEvent.click(box);
    expect(onSelect).toHaveBeenCalledWith(JOURNEY_VIEW.stops[0]?.stopPoint.element?.id);
  });

  it("markiert die gewählte Box", () => {
    const journeyId = JOURNEY_VIEW.journey.id;
    renderOverview(JOURNEY_VIEW, journeyId);
    expect(document.querySelector(".struct-box.selected")?.textContent).toContain("ServiceJourney");
  });

  it("kennzeichnet nicht aufgelöste Verweise und fehlende Angaben ohne Farbe und Klick", () => {
    renderOverview({
      ...JOURNEY_VIEW,
      pattern: { status: "not_resolved", text: "sjp-x", element: null },
      validities: [],
    });
    const stops = screen.getByRole("region", { name: "Halte, Gleise und Haltestellen" });
    const missing = within(stops).getByText("ServiceJourneyPattern").closest("div") as HTMLElement;
    expect(missing.className).toContain("struct-missing");
    expect(within(missing).getByText("nicht gefunden")).toBeTruthy();
    expect(missing.getAttribute("title")).toBe("sjp-x: nicht in dieser Datei aufgelöst");
    const days = screen.getByRole("region", { name: "Betriebstage" });
    expect(within(days).getByText("nicht in der Datei")).toBeTruthy();
  });

  it("zeigt abgeleitete Zahlen als neutrale Boxen ohne Klick", () => {
    renderOverview();
    const times = screen.getByRole("region", { name: "Zeiten" });
    const derived = within(times).getByText("Berechnete Zeiten: 2").closest("div") as HTMLElement;
    expect(derived.className).toContain("struct-derived");
    expect(within(times).getByText("Nicht berechenbare Zeiten: 1")).toBeTruthy();
  });
});

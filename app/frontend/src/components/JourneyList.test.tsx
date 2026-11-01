import { fireEvent, render, screen } from "@testing-library/react";
import { JOURNEYS } from "../testData";
import type { JourneyInfo } from "../types";
import { JourneyList } from "./JourneyList";

const JOURNEY = JOURNEYS[0] as JourneyInfo;

function renderList(journeys: JourneyInfo[] | null, errorKey: string | null = null) {
  const onOpenJourney = vi.fn();
  render(
    <JourneyList
      journeys={journeys}
      errorKey={errorKey}
      selected={null}
      onOpenJourney={onOpenJourney}
    />,
  );
  return onOpenJourney;
}

describe("JourneyList", () => {
  it("zeigt Abzeichen, Zugnummer, Abfahrt und Strecke einspaltig und öffnet die Fahrt", () => {
    const onOpenJourney = renderList([JOURNEY]);
    expect(screen.getByText("SYN").className).toContain("badge");
    expect(screen.getByText("08:00")).toBeTruthy();
    expect(screen.queryByText(/DepartureDayOffset/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Synthetisch A/ }));
    expect(onOpenJourney).toHaveBeenCalledWith(JOURNEY.object.id);
  });

  it("zeigt Verschiebungen als „+1“ und keine Marke bei 0 oder ungültigem Wert", () => {
    const offset = (text: string): JourneyInfo => ({
      ...JOURNEY,
      departureDayOffset: { status: "found", text, objectId: null },
    });
    renderList([offset("1")]);
    expect(screen.getByText("+1")).toBeTruthy();
  });

  it("lässt die Marke bei ungültigem Wert weg", () => {
    renderList([
      { ...JOURNEY, departureDayOffset: { status: "found", text: "x", objectId: null } },
    ]);
    expect(document.querySelector(".day-marker")).toBeNull();
  });

  it("kennzeichnet fehlende Angaben, statt etwas zu ergänzen", () => {
    renderList([
      {
        ...JOURNEY,
        trainNumbers: [],
        category: { status: "absent", text: null, objectId: null },
        departureTime: { status: "absent", text: null, objectId: null },
      },
    ]);
    expect(document.querySelector(".category-badge")).toBeNull();
    expect(screen.getAllByText("nicht in der Datei").length).toBe(2);
  });

  it("meldet Fehler und leere Dateien", () => {
    renderList(null, "error.not_found");
    expect(screen.getByRole("alert").textContent).toContain("Nicht gefunden");
  });

  it("sagt, wenn die Datei keine Fahrten enthält", () => {
    renderList([]);
    expect(screen.getByText("Diese Datei enthält keine Fahrten.")).toBeTruthy();
  });
});

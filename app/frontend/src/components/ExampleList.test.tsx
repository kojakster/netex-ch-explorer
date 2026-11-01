import { fireEvent, render, screen } from "@testing-library/react";
import { GUIDE } from "../testData";
import type { ExampleInfo } from "../types";
import { ExampleList, exampleStatusSymbol } from "./ExampleList";

const BASE = GUIDE.examples[0] as ExampleInfo;

describe("ExampleList", () => {
  it("hebt das Beispiel mit dem Präfix 01_ als Einstieg hervor, nicht nach dem Titel", () => {
    const examples = [
      { ...BASE, name: "01_einfach.xml", title: "Egal was hier steht" },
      { ...BASE, name: "02_anders.xml", title: "Hier beginnen: einfache Zugfahrt" },
    ];
    render(<ExampleList examples={examples} selected={null} onOpen={() => undefined} />);
    const hints = screen.getAllByText("Hier beginnen: einfache Zugfahrt");
    // Der Titel von 02 ist nur Text; die Hervorhebung gehört allein zu 01.
    expect(hints.length).toBe(2);
    expect(
      screen.getByText("01_einfach.xml").closest("button")?.className.includes("example-start"),
    ).toBe(true);
    expect(
      screen.getByText("02_anders.xml").closest("button")?.className.includes("example-start"),
    ).toBe(false);
  });

  it("öffnet ein Beispiel und zeigt Beschreibung und Status", () => {
    const onOpen = vi.fn();
    render(<ExampleList examples={GUIDE.examples} selected={null} onOpen={onOpen} />);
    expect(screen.getByText("Synthetische Fahrt")).toBeTruthy();
    expect(screen.getByText("ohne Meldungen")).toBeTruthy();
    fireEvent.click(screen.getByText("ch20_three_stops.xml"));
    expect(onOpen).toHaveBeenCalledWith("ch20_three_stops.xml");
  });

  it("meldet, wenn es keine Beispiele gibt", () => {
    render(<ExampleList examples={[]} selected={null} onOpen={() => undefined} />);
    expect(screen.getByText("Keine Beispiele gefunden.")).toBeTruthy();
  });
});

describe("exampleStatusSymbol", () => {
  it("hat für jedes Ergebnis ein Symbol, solange geprüft wird keines", () => {
    const results = ["clean", "notes", "errors", "check_failed", "unreadable"] as const;
    for (const result of results) {
      expect(exampleStatusSymbol({ ...BASE, result })).not.toBe("");
    }
    expect(exampleStatusSymbol({ ...BASE, result: null })).toBe("");
  });
});

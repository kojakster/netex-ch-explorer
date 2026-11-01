import { fireEvent, render, screen } from "@testing-library/react";
import { GUIDE } from "../testData";
import { DatasetPicker } from "./DatasetPicker";

describe("DatasetPicker", () => {
  it("listet die Beispiele mit Status und öffnet das gewählte", () => {
    const onOpenExample = vi.fn();
    render(
      <DatasetPicker
        examples={GUIDE.examples}
        selected={null}
        onOpenExample={onOpenExample}
        onOpenFiles={() => undefined}
      />,
    );
    expect(screen.getByRole("option", { name: "✔ ch20_three_stops.xml" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "✖ broken_xml.xml" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Datensatz"), {
      target: { value: "broken_xml.xml" },
    });
    expect(onOpenExample).toHaveBeenCalledWith("broken_xml.xml");
  });

  it("öffnet bei der Platzhalter-Auswahl nichts und bietet „Datei öffnen …“ an", () => {
    const onOpenExample = vi.fn();
    render(
      <DatasetPicker
        examples={GUIDE.examples}
        selected="ch20_three_stops.xml"
        onOpenExample={onOpenExample}
        onOpenFiles={() => undefined}
      />,
    );
    expect((screen.getByLabelText("Datensatz") as HTMLSelectElement).value).toBe(
      "ch20_three_stops.xml",
    );
    fireEvent.change(screen.getByLabelText("Datensatz"), { target: { value: "" } });
    expect(onOpenExample).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Datei öffnen …" })).toBeTruthy();
  });
});

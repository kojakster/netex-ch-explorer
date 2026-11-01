import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { DataSource } from "../api";
import { DataSourceContext } from "../data";
import { APP_INFO, DATASET, fakeSource, OBJECT_TREE } from "../testData";
import { ObjectTree } from "./ObjectTree";

function renderTree(source: DataSource = fakeSource(), onSelect: (id: string) => void = () => {}) {
  render(
    <DataSourceContext.Provider value={source}>
      <ObjectTree dataset={DATASET} colors={APP_INFO.frameColors} onSelect={onSelect} />
    </DataSourceContext.Provider>,
  );
}

describe("ObjectTree", () => {
  it("zeigt den Frame in seiner Farbe und die Objekte darunter eingerückt", async () => {
    renderTree();
    const frame = (await screen.findByText("TimetableFrame")).closest("li");
    expect(frame?.className).toContain("tree-frame");
    expect(frame?.style.backgroundColor).toBe("rgb(0, 87, 184)");
    expect(frame?.style.color).toBe("rgb(255, 255, 255)");
    const stopPlace = screen.getByText("StopPlace").closest("li");
    const quay = screen.getByText("Quay").closest("li");
    expect(stopPlace?.style.marginInlineStart).toBe("0.9rem");
    expect(quay?.style.marginInlineStart).toBe("1.8rem");
    expect(screen.getByText("3 Objekte")).toBeTruthy();
  });

  it("kennzeichnet übergeordnete Objekte, Grau-Elemente und die Gruppe ausserhalb", async () => {
    renderTree();
    await screen.findByText("Quay");
    expect(screen.getByText("Quay").closest("li")?.className).toContain("tree-context");
    expect(screen.getByText("StopPlace").closest("li")?.className).not.toContain("tree-context");
    expect(screen.getByText("für den Fahrplan nicht relevant")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Ausserhalb eines Frames" })).toBeTruthy();
    expect(screen.getByText("Loose")).toBeTruthy();
  });

  it("klappt einen Frame mit der Tastatur zu und wieder auf", async () => {
    renderTree();
    const toggle = await screen.findByRole("button", { name: "TimetableFrame zuklappen" });
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(toggle);
    expect(screen.queryByText("StopPlace")).toBeNull();
    const closed = screen.getByRole("button", { name: "TimetableFrame aufklappen" });
    expect(closed.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(closed);
    expect(screen.getByText("StopPlace")).toBeTruthy();
  });

  it("öffnet ein Objekt und einen Frame mit einem Klick", async () => {
    const onSelect = vi.fn();
    renderTree(fakeSource(), onSelect);
    fireEvent.click(await screen.findByText("StopPlace"));
    fireEvent.click(screen.getByText("TimetableFrame"));
    expect(onSelect.mock.calls.map(([id]) => id)).toEqual([
      "SYNTHETICDATASET01.2",
      "SYNTHETICDATASET01.1",
    ]);
  });

  it("fragt mit dem Filter neu ab", async () => {
    const getObjectTree = vi.fn(() => Promise.resolve(OBJECT_TREE));
    renderTree(fakeSource({ getObjectTree }));
    await screen.findByText("Quay");
    fireEvent.change(screen.getByLabelText("ID oder Name enthält"), { target: { value: " 8 " } });
    await waitFor(() =>
      expect(getObjectTree).toHaveBeenLastCalledWith(DATASET.id, { type: "", q: "8" }),
    );
    fireEvent.change(screen.getByLabelText("Typ"), { target: { value: "ServiceJourney" } });
    await waitFor(() =>
      expect(getObjectTree).toHaveBeenLastCalledWith(DATASET.id, {
        type: "ServiceJourney",
        q: "8",
      }),
    );
  });

  it("meldet Kürzung, leere Ergebnisse und Fehler", async () => {
    const truncated = { ...OBJECT_TREE, total: 9000, shown: 5, truncated: true };
    renderTree(fakeSource({ getObjectTree: () => Promise.resolve(truncated) }));
    expect(await screen.findByRole("status")).toBeTruthy();
    expect(screen.getByText(/Nur die ersten 5 von 9000 Treffern/)).toBeTruthy();
  });

  it("zeigt bei leerem Ergebnis einen Hinweis", async () => {
    const empty = { entries: [], outside: [], total: 0, shown: 0, truncated: false };
    renderTree(fakeSource({ getObjectTree: () => Promise.resolve(empty) }));
    expect(await screen.findByText("Keine Objekte gefunden.")).toBeTruthy();
  });

  it("zeigt Ladefehler", async () => {
    renderTree(fakeSource({ getObjectTree: () => Promise.reject(new Error("x")) }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});

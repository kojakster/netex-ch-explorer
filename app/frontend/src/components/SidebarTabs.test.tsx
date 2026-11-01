import { fireEvent, render, screen } from "@testing-library/react";
import { type SidebarTab, SidebarTabs, tabAfterKey } from "./SidebarTabs";

function renderTabs(active: SidebarTab, onChange: (tab: SidebarTab) => void = () => undefined) {
  render(
    <SidebarTabs active={active} onChange={onChange} findingCount={null}>
      <p>Inhalt</p>
    </SidebarTabs>,
  );
}

describe("tabAfterKey", () => {
  it("wechselt mit den Pfeiltasten im Kreis und mit Pos1/Ende an die Enden", () => {
    expect(tabAfterKey("journeys", "ArrowRight")).toBe("objects");
    expect(tabAfterKey("check", "ArrowRight")).toBe("journeys");
    expect(tabAfterKey("journeys", "ArrowLeft")).toBe("check");
    expect(tabAfterKey("objects", "Home")).toBe("journeys");
    expect(tabAfterKey("objects", "End")).toBe("check");
  });

  it("ignoriert andere Tasten", () => {
    expect(tabAfterKey("objects", "a")).toBeNull();
  });
});

describe("SidebarTabs", () => {
  it("macht nur den gewählten Reiter mit der Tabulatortaste erreichbar", () => {
    renderTabs("objects");
    expect(screen.getByRole("tab", { name: "Objekte" }).getAttribute("tabindex")).toBe("0");
    expect(screen.getByRole("tab", { name: "Fahrten" }).getAttribute("tabindex")).toBe("-1");
  });

  it("wechselt mit der Pfeiltaste den Reiter und setzt den Fokus darauf", () => {
    const onChange = vi.fn();
    renderTabs("journeys", onChange);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Fahrten" }), { key: "ArrowRight" });
    expect(onChange).toHaveBeenCalledWith("objects");
    expect(document.activeElement).toBe(screen.getByRole("tab", { name: "Objekte" }));
  });

  it("lässt andere Tasten unberührt", () => {
    const onChange = vi.fn();
    renderTabs("journeys", onChange);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Fahrten" }), { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });
});

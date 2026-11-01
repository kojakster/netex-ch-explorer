import { fireEvent, render, screen } from "@testing-library/react";
import { ResizeHandle } from "./ResizeHandle";

function renderHandle(columnOnLeft: boolean) {
  const onChange = vi.fn();
  const onReset = vi.fn();
  render(
    <ResizeHandle
      labelKey="resize.sidebar"
      width={300}
      min={200}
      max={500}
      columnOnLeft={columnOnLeft}
      onChange={onChange}
      onReset={onReset}
    />,
  );
  return { handle: screen.getByRole("separator"), onChange, onReset };
}

describe("ResizeHandle", () => {
  it("ist ein fokussierbarer senkrechter Trenner mit Werten und Beschriftung", () => {
    const { handle } = renderHandle(true);
    expect(handle.getAttribute("aria-orientation")).toBe("vertical");
    expect(handle.getAttribute("aria-valuenow")).toBe("300");
    expect(handle.getAttribute("aria-valuemin")).toBe("200");
    expect(handle.getAttribute("aria-valuemax")).toBe("500");
    expect(handle.getAttribute("aria-label")).toBe("Breite der Navigation");
    expect(handle.getAttribute("tabindex")).toBe("0");
  });

  it("verstellt mit den Pfeiltasten, Pos1 und Ende", () => {
    const { handle, onChange } = renderHandle(true);
    fireEvent.keyDown(handle, { key: "ArrowRight" });
    fireEvent.keyDown(handle, { key: "ArrowLeft", shiftKey: true });
    fireEvent.keyDown(handle, { key: "Home" });
    fireEvent.keyDown(handle, { key: "End" });
    expect(onChange.mock.calls.map(([width]) => width)).toEqual([316, 236, 200, 500]);
  });

  it("ignoriert andere Tasten", () => {
    const { handle, onChange } = renderHandle(true);
    fireEvent.keyDown(handle, { key: "Enter" });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("verbreitert beim Ziehen nach rechts, wenn die Spalte links liegt, und klemmt", () => {
    const { handle, onChange } = renderHandle(true);
    fireEvent.pointerDown(handle, { clientX: 100, pointerId: 1, button: 0 });
    fireEvent.pointerMove(handle, { clientX: 150, pointerId: 1 });
    fireEvent.pointerMove(handle, { clientX: 900, pointerId: 1 });
    fireEvent.pointerMove(handle, { clientX: -900, pointerId: 1 });
    expect(onChange.mock.calls.map(([width]) => width)).toEqual([350, 500, 200]);
  });

  it("verkleinert beim Ziehen nach rechts, wenn die Spalte rechts liegt", () => {
    const { handle, onChange } = renderHandle(false);
    fireEvent.pointerDown(handle, { clientX: 100, pointerId: 1, button: 0 });
    fireEvent.pointerMove(handle, { clientX: 150, pointerId: 1 });
    expect(onChange).toHaveBeenLastCalledWith(250);
  });

  it("reagiert nach dem Loslassen oder ohne Drücken nicht auf Bewegung", () => {
    const { handle, onChange } = renderHandle(true);
    fireEvent.pointerMove(handle, { clientX: 150, pointerId: 1 });
    fireEvent.pointerDown(handle, { clientX: 100, pointerId: 1, button: 0 });
    fireEvent.pointerUp(handle, { pointerId: 1 });
    fireEvent.pointerMove(handle, { clientX: 150, pointerId: 1 });
    fireEvent.pointerDown(handle, { clientX: 100, pointerId: 1, button: 2 });
    fireEvent.pointerMove(handle, { clientX: 150, pointerId: 1 });
    fireEvent.pointerCancel(handle, { pointerId: 1 });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("setzt mit Doppelklick die Standardbreite zurück", () => {
    const { handle, onReset } = renderHandle(true);
    fireEvent.doubleClick(handle);
    expect(onReset).toHaveBeenCalledOnce();
  });
});

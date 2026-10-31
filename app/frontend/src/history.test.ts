import {
  canGoBack,
  canGoForward,
  currentSelection,
  EMPTY_HISTORY,
  goBack,
  goForward,
  visit,
} from "./history";

const A = { objectId: "a", elementId: "a" };
const B = { objectId: "b", elementId: "b" };
const C = { objectId: "b", elementId: "b.1" };

describe("Verlauf", () => {
  it("ist am Anfang leer", () => {
    expect(currentSelection(EMPTY_HISTORY)).toBeNull();
    expect(canGoBack(EMPTY_HISTORY)).toBe(false);
    expect(canGoForward(EMPTY_HISTORY)).toBe(false);
    expect(goBack(EMPTY_HISTORY)).toBe(EMPTY_HISTORY);
    expect(goForward(EMPTY_HISTORY)).toBe(EMPTY_HISTORY);
  });

  it("geht vor und zurück", () => {
    const history = visit(visit(visit(EMPTY_HISTORY, A), B), C);
    expect(currentSelection(history)).toEqual(C);
    const back = goBack(goBack(history));
    expect(currentSelection(back)).toEqual(A);
    expect(canGoBack(back)).toBe(false);
    expect(canGoForward(back)).toBe(true);
    expect(currentSelection(goForward(back))).toEqual(B);
  });

  it("verwirft Einträge nach dem Zurückgehen bei einem neuen Besuch", () => {
    const history = visit(goBack(visit(visit(EMPTY_HISTORY, A), B)), C);
    expect(history.entries).toEqual([A, C]);
    expect(canGoForward(history)).toBe(false);
  });

  it("legt dieselbe Auswahl nicht doppelt ab", () => {
    const history = visit(EMPTY_HISTORY, A);
    expect(visit(history, A)).toBe(history);
  });

  it("bleibt an den Enden stehen", () => {
    const history = visit(EMPTY_HISTORY, A);
    expect(goBack(history)).toBe(history);
    expect(goForward(history)).toBe(history);
  });
});

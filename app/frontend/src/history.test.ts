import {
  canGoBack,
  canGoForward,
  currentSelection,
  EMPTY_HISTORY,
  goBack,
  goForward,
  type Selection,
  visit,
} from "./history";

const A: Selection = { objectId: "a", elementId: "a", view: "object", timeId: null };
const B: Selection = { objectId: "b", elementId: "b", view: "object", timeId: null };
const C: Selection = { objectId: "b", elementId: "b.1", view: "object", timeId: null };

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

  it("unterscheidet Ansicht und gewählte Zeit derselben Angabe", () => {
    const journey: Selection = { ...A, view: "journey" };
    const timed: Selection = { ...journey, timeId: "arrival-2" };
    const history = visit(visit(visit(EMPTY_HISTORY, A), journey), timed);
    expect(history.entries).toEqual([A, journey, timed]);
    expect(visit(history, timed)).toBe(history);
  });

  it("bleibt an den Enden stehen", () => {
    const history = visit(EMPTY_HISTORY, A);
    expect(goBack(history)).toBe(history);
    expect(goForward(history)).toBe(history);
  });
});

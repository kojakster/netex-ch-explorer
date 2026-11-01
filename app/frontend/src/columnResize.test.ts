import { act, renderHook } from "@testing-library/react";
import {
  clampWidth,
  columnLayout,
  DETAILS_LIMITS,
  KEY_STEP,
  KEY_STEP_LARGE,
  MAIN_MIN_WIDTH,
  maxWidthFor,
  parseStoredWidth,
  SIDEBAR_LIMITS,
  useStoredWidth,
  useViewportWidth,
  widthAfterKey,
} from "./columnResize";

const KEY = "test.width";

afterEach(() => {
  window.localStorage.clear();
  vi.restoreAllMocks();
});

describe("clampWidth", () => {
  it("klemmt auf die Grenzen und rundet", () => {
    expect(clampWidth(100, 200, 400)).toBe(200);
    expect(clampWidth(900, 200, 400)).toBe(400);
    expect(clampWidth(250.6, 200, 400)).toBe(251);
  });

  it("nimmt das Minimum, wenn das Maximum darunter liegt", () => {
    expect(clampWidth(300, 200, 150)).toBe(200);
  });
});

describe("widthAfterKey", () => {
  it("verändert die Breite in Schritten, mit Umschalttaste grösser", () => {
    expect(widthAfterKey("ArrowRight", false, 300, 200, 500, true)).toBe(300 + KEY_STEP);
    expect(widthAfterKey("ArrowLeft", false, 300, 200, 500, true)).toBe(300 - KEY_STEP);
    expect(widthAfterKey("ArrowRight", true, 300, 200, 500, true)).toBe(300 + KEY_STEP_LARGE);
  });

  it("kehrt die Richtung um, wenn die Spalte rechts vom Griff liegt", () => {
    expect(widthAfterKey("ArrowRight", false, 300, 200, 500, false)).toBe(300 - KEY_STEP);
    expect(widthAfterKey("ArrowLeft", false, 300, 200, 500, false)).toBe(300 + KEY_STEP);
  });

  it("klemmt, und Pos1/Ende setzen Minimum und Maximum", () => {
    expect(widthAfterKey("ArrowRight", false, 495, 200, 500, true)).toBe(500);
    expect(widthAfterKey("ArrowLeft", false, 205, 200, 500, true)).toBe(200);
    expect(widthAfterKey("Home", false, 300, 200, 500, true)).toBe(200);
    expect(widthAfterKey("End", false, 300, 200, 500, true)).toBe(500);
  });

  it("ignoriert andere Tasten", () => {
    expect(widthAfterKey("a", false, 300, 200, 500, true)).toBeNull();
  });
});

describe("parseStoredWidth", () => {
  it("liest nur ganze Zahlen", () => {
    expect(parseStoredWidth("300")).toBe(300);
    expect(parseStoredWidth(null)).toBeNull();
    expect(parseStoredWidth("")).toBeNull();
    expect(parseStoredWidth("-5")).toBeNull();
    expect(parseStoredWidth("3.5")).toBeNull();
    expect(parseStoredWidth("abc")).toBeNull();
    expect(parseStoredWidth("1e3")).toBeNull();
    expect(parseStoredWidth("123456")).toBeNull();
  });
});

describe("maxWidthFor", () => {
  it("lässt dem Hauptbereich seine Mindestbreite", () => {
    const max = maxWidthFor(SIDEBAR_LIMITS, 1400, DETAILS_LIMITS.min, 2);
    expect(1400 - max - DETAILS_LIMITS.min).toBeGreaterThanOrEqual(MAIN_MIN_WIDTH);
    expect(max).toBeGreaterThanOrEqual(SIDEBAR_LIMITS.min);
    expect(max).toBeLessThanOrEqual(SIDEBAR_LIMITS.max);
  });

  it("fällt nie unter das Minimum", () => {
    expect(maxWidthFor(SIDEBAR_LIMITS, 300, 0, 1)).toBe(SIDEBAR_LIMITS.min);
  });
});

describe("columnLayout", () => {
  it("zeigt beide Griffe in einem breiten Fenster und hält die Mindestbreite des Hauptbereichs", () => {
    const layout = columnLayout(1500, true, true, SIDEBAR_LIMITS.max, DETAILS_LIMITS.max);
    expect(layout.sidebar.handle && layout.details.handle).toBe(true);
    const main = 1500 - 32 - 40 - layout.sidebar.width - layout.details.width;
    expect(main).toBeGreaterThanOrEqual(MAIN_MIN_WIDTH);
  });

  it("blendet die rechte Spalte unter 1280 px und alle Griffe unter 801 px aus", () => {
    const wrapped = columnLayout(1100, true, true, 300, 400);
    expect(wrapped.sidebar.handle).toBe(true);
    expect(wrapped.details.handle).toBe(false);
    const narrow = columnLayout(700, true, true, 300, 400);
    expect(narrow.sidebar.handle || narrow.details.handle).toBe(false);
  });

  it("zeigt ohne Datensatz und ohne Auswahl keine Griffe", () => {
    const layout = columnLayout(1500, false, false, 300, 400);
    expect(layout.sidebar.handle || layout.details.handle).toBe(false);
  });

  it("belässt gespeicherte Breiten innerhalb der Grenzen unverändert", () => {
    const layout = columnLayout(1600, true, true, 300, 450);
    expect([layout.sidebar.width, layout.details.width]).toEqual([300, 450]);
  });
});

describe("useStoredWidth", () => {
  it("beginnt mit dem Standard, wenn nichts gespeichert ist", () => {
    const { result } = renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS));
    expect(result.current[0]).toBe(SIDEBAR_LIMITS.initial);
  });

  it("liest eine gespeicherte Breite und klemmt sie auf die Grenzen", () => {
    window.localStorage.setItem(KEY, "350");
    expect(renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS)).result.current[0]).toBe(350);
    window.localStorage.setItem(KEY, "99999");
    expect(renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS)).result.current[0]).toBe(
      SIDEBAR_LIMITS.max,
    );
    window.localStorage.setItem(KEY, "10");
    expect(renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS)).result.current[0]).toBe(
      SIDEBAR_LIMITS.min,
    );
  });

  it("ignoriert ungültige Werte", () => {
    window.localStorage.setItem(KEY, "breit");
    expect(renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS)).result.current[0]).toBe(
      SIDEBAR_LIMITS.initial,
    );
  });

  it("merkt die gesetzte Breite (geklemmt) und stellt den Standard wieder her", () => {
    const { result } = renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS));
    act(() => result.current[1](333));
    expect(result.current[0]).toBe(333);
    expect(window.localStorage.getItem(KEY)).toBe("333");
    act(() => result.current[1](10_000));
    expect(result.current[0]).toBe(SIDEBAR_LIMITS.max);
    act(() => result.current[2]());
    expect(result.current[0]).toBe(SIDEBAR_LIMITS.initial);
    expect(window.localStorage.getItem(KEY)).toBeNull();
  });

  it("funktioniert auch, wenn der Speicher nicht zugänglich ist", () => {
    for (const method of ["getItem", "setItem", "removeItem"] as const) {
      vi.spyOn(Storage.prototype, method).mockImplementation(() => {
        throw new Error("gesperrt");
      });
    }
    const { result } = renderHook(() => useStoredWidth(KEY, SIDEBAR_LIMITS));
    expect(result.current[0]).toBe(SIDEBAR_LIMITS.initial);
    act(() => result.current[1](300));
    expect(result.current[0]).toBe(300);
    act(() => result.current[2]());
    expect(result.current[0]).toBe(SIDEBAR_LIMITS.initial);
  });
});

describe("useViewportWidth", () => {
  it("folgt der Fensterbreite", () => {
    const { result } = renderHook(() => useViewportWidth());
    expect(result.current).toBe(window.innerWidth);
    act(() => {
      Object.defineProperty(window, "innerWidth", { value: 900, configurable: true });
      window.dispatchEvent(new Event("resize"));
    });
    expect(result.current).toBe(900);
  });
});

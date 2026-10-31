import { dayMarker, formatDate, shortCommit, timeWithDay, trimSeconds } from "./format";

describe("Zeitdarstellung", () => {
  it("kürzt volle Minuten", () => {
    expect(trimSeconds("10:35:00")).toBe("10:35");
    expect(trimSeconds("10:35:10")).toBe("10:35:10");
  });

  it("markiert den Tageswechsel", () => {
    expect(dayMarker(0)).toBe("");
    expect(dayMarker(1)).toBe("+1");
    expect(dayMarker(2)).toBe("+2");
    expect(dayMarker(-1)).toBe("−1");
    expect(timeWithDay("00:17:00", 1)).toBe("00:17 +1");
    expect(timeWithDay("08:00:00", 0)).toBe("08:00");
  });

  it("formatiert Daten nach Sprache", () => {
    expect(formatDate("2026-12-14", "de-CH")).toBe("14.12.2026");
    expect(formatDate("2026-12-14", "en")).toBe("2026-12-14");
    expect(formatDate("kein Datum", "de-CH")).toBe("kein Datum");
  });

  it("kürzt Commits", () => {
    expect(shortCommit("b7ac15860369818a")).toBe("b7ac158");
    expect(shortCommit(null)).toBe("");
  });
});

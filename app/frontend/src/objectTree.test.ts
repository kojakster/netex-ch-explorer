import { COLLAPSE_THRESHOLD, isFrameOpen, objectCountBelow, visibleEntries } from "./objectTree";
import { JOURNEY_OBJECT } from "./testData";
import type { ObjectTreeEntry } from "./types";

function entry(id: string, depth: number, isFrame = false): ObjectTreeEntry {
  return { object: { ...JOURNEY_OBJECT, id }, isFrame, depth, matches: true };
}

// Frame A (Objekt, Unterobjekt, verschachtelter Frame B mit Objekt), Frame C (Objekt)
const ENTRIES = [
  entry("A", 0, true),
  entry("a1", 1),
  entry("a1x", 2),
  entry("B", 1, true),
  entry("b1", 2),
  entry("C", 0, true),
  entry("c1", 1),
];

describe("objectCountBelow", () => {
  it("zählt Objekte, nicht Frames, auch in verschachtelten Frames", () => {
    expect(objectCountBelow(ENTRIES, 0)).toBe(3);
    expect(objectCountBelow(ENTRIES, 3)).toBe(1);
    expect(objectCountBelow(ENTRIES, 5)).toBe(1);
    expect(objectCountBelow(ENTRIES, 99)).toBe(0);
  });
});

describe("isFrameOpen", () => {
  it("folgt der Wahl, sonst der Schwelle", () => {
    expect(isFrameOpen(undefined, COLLAPSE_THRESHOLD)).toBe(true);
    expect(isFrameOpen(undefined, COLLAPSE_THRESHOLD + 1)).toBe(false);
    expect(isFrameOpen(true, COLLAPSE_THRESHOLD + 1)).toBe(true);
    expect(isFrameOpen(false, 1)).toBe(false);
  });
});

describe("visibleEntries", () => {
  it("zeigt standardmässig alles", () => {
    const rows = visibleEntries(ENTRIES, new Map());
    expect(rows.map((row) => row.entry.object.id)).toEqual([
      "A",
      "a1",
      "a1x",
      "B",
      "b1",
      "C",
      "c1",
    ]);
    expect(rows[0]?.objectCount).toBe(3);
  });

  it("blendet unter einem zugeklappten Frame alles Tiefere aus", () => {
    const rows = visibleEntries(ENTRIES, new Map([["A", false]]));
    expect(rows.map((row) => row.entry.object.id)).toEqual(["A", "C", "c1"]);
    expect(rows[0]?.open).toBe(false);
  });

  it("klappt nur den verschachtelten Frame zu", () => {
    const rows = visibleEntries(ENTRIES, new Map([["B", false]]));
    expect(rows.map((row) => row.entry.object.id)).toEqual(["A", "a1", "a1x", "B", "C", "c1"]);
  });

  it("startet Frames über der Schwelle zugeklappt", () => {
    const rows = visibleEntries(ENTRIES, new Map(), 2);
    expect(rows.map((row) => row.entry.object.id)).toEqual(["A", "C", "c1"]);
  });
});

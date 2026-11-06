import { formatCommitDate } from "./commitDate";

describe("formatCommitDate", () => {
  it("zeigt Datum und Uhrzeit des Commits ohne Umrechnung der Zeitzone", () => {
    expect(formatCommitDate("2026-11-04T09:16:10+01:00", "de-CH")).toBe("04.11.2026 09:16");
    expect(formatCommitDate("2026-11-04T23:59:59-05:00", "de-CH")).toBe("04.11.2026 23:59");
  });

  it("nutzt in anderen Sprachen die ISO-Reihenfolge", () => {
    expect(formatCommitDate("2026-11-04T09:16:10+01:00", "en")).toBe("2026-11-04 09:16");
  });

  it("liefert null bei ungültiger Angabe", () => {
    expect(formatCommitDate("gestern", "de-CH")).toBeNull();
    expect(formatCommitDate("", "en")).toBeNull();
  });
});

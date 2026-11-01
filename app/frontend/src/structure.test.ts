import { buildStructure, type StructureRow } from "./structure";
import { JOURNEY_VIEW } from "./testData";
import type { JourneyViewInfo, ObjectInfo, StopInfo, ValueInfo } from "./types";

function row(view: JourneyViewInfo, id: StructureRow["id"]): StructureRow {
  const found = buildStructure(view).find((item) => item.id === id);
  if (found === undefined) {
    throw new Error(`Zeile ${id} fehlt`);
  }
  return found;
}

function names(item: StructureRow): string[][] {
  return item.steps.map((step) => step.map((box) => box.netex ?? box.text?.key ?? ""));
}

const ABSENT: ValueInfo = { status: "absent", text: null, element: null };

describe("buildStructure", () => {
  it("liefert die vier Zeilen in fester Reihenfolge", () => {
    expect(buildStructure(JOURNEY_VIEW).map((item) => item.id)).toEqual([
      "stops",
      "times",
      "days",
      "master",
    ]);
  });

  it("verbindet Fahrt, Fahrtmuster, Fahrplanpunkte, Zuordnung und Gleis/Haltestelle", () => {
    const stops = row(JOURNEY_VIEW, "stops");
    expect(names(stops)).toEqual([
      ["ServiceJourney"],
      ["ServiceJourneyPattern"],
      ["ScheduledStopPoint"],
      ["PassengerStopAssignment"],
      ["Quay", "StopPlace"],
    ]);
    const points = stops.steps[2]?.[0];
    expect(points?.text).toEqual({ key: "structure.count", params: { count: 3, missing: 0 } });
    expect(points?.object?.colorKey).toBe("ServiceFrame");
  });

  it("meldet ein nicht aufgelöstes Fahrtmuster und zeigt dann keine Halte", () => {
    const missing: ValueInfo = { status: "not_resolved", text: "sjp-x", element: null };
    const stops = row({ ...JOURNEY_VIEW, pattern: missing }, "stops");
    expect(names(stops)).toEqual([["ServiceJourney"], ["ServiceJourneyPattern"]]);
    expect(stops.steps[1]?.[0]?.problem).toBe("not_resolved");
    const absent = row({ ...JOURNEY_VIEW, pattern: ABSENT }, "stops");
    expect(absent.steps[1]?.[0]?.problem).toBe("absent");
  });

  it("zählt Halte ohne Zuordnung als nicht gefunden und meldet fehlende Haltestellen", () => {
    const [first, ...rest] = JOURNEY_VIEW.stops as [StopInfo, ...StopInfo[]];
    const external: ValueInfo = { status: "external_or_unloaded", text: "x", element: null };
    const stops = [{ ...first, assignment: null, stopPlace: external, quay: external }, ...rest];
    const result = row({ ...JOURNEY_VIEW, stops }, "stops");
    const assignment = result.steps[3]?.[0];
    expect(assignment?.text?.key).toBe("structure.countMissing");
    expect(assignment?.text?.params).toEqual({ count: 2, missing: 1 });
    const everythingExternal = JOURNEY_VIEW.stops.map((stop) => ({
      ...stop,
      assignment: null,
      stopPlace: external,
      quay: external,
    }));
    const none = row({ ...JOURNEY_VIEW, stops: everythingExternal }, "stops");
    expect(none.steps[3]?.[0]?.problem).toBe("absent");
    expect(none.steps[4]?.map((box) => box.problem)).toEqual([
      "external_or_unloaded",
      "external_or_unloaded",
    ]);
  });

  it("zeigt TimeDemandType, Fahr- und Wartezeiten und die berechneten Zeiten", () => {
    const times = row(JOURNEY_VIEW, "times");
    expect(times.steps[0]?.[0]?.netex).toBe("ServiceJourney");
    expect(times.steps[1]?.[0]?.netex).toBe("TimeDemandType");
    const last = times.steps[times.steps.length - 1] ?? [];
    expect(last.map((box) => box.text?.key)).toEqual([
      "structure.times.explicit",
      "structure.times.computed",
      "structure.times.failed",
    ]);
    expect(last.every((box) => box.object === null)).toBe(true);
  });

  it("lässt bei Zeiten ohne TimeDemandType dessen Box weg, meldet aber ein nicht aufgelöstes", () => {
    const without = row({ ...JOURNEY_VIEW, timeDemandType: ABSENT }, "times");
    expect(without.steps.flat().some((box) => box.netex === "TimeDemandType")).toBe(false);
    const broken: ValueInfo = { status: "not_resolved", text: "tdt-x", element: null };
    const unresolved = row({ ...JOURNEY_VIEW, timeDemandType: broken }, "times");
    expect(unresolved.steps[1]?.[0]).toMatchObject({
      netex: "TimeDemandType",
      problem: "not_resolved",
    });
  });

  it("zeigt Bedingung und ValidDayBits mit Anzahl der Betriebstage", () => {
    const days = row(JOURNEY_VIEW, "days");
    expect(names(days)).toEqual([["ServiceJourney"], ["AvailabilityCondition"], ["ValidDayBits"]]);
    expect(days.steps[2]?.[0]?.text).toEqual({
      key: "structure.days.count",
      params: { count: 5 },
    });
  });

  it("meldet fehlende und nicht aufgelöste Betriebstage", () => {
    const none = row({ ...JOURNEY_VIEW, validities: [] }, "days");
    expect(none.steps[1]?.[0]).toMatchObject({ netex: "AvailabilityCondition", problem: "absent" });
    const validity = JOURNEY_VIEW.validities[0];
    if (validity === undefined) {
      throw new Error("Testdaten ohne Betriebstage");
    }
    const unresolved = row(
      {
        ...JOURNEY_VIEW,
        validities: [
          {
            ref: validity.ref,
            days: null,
            problem: { status: "not_resolved", text: "ac-x", element: validity.ref },
          },
          { ref: validity.ref, days: null, problem: null },
        ],
      },
      "days",
    );
    expect(unresolved.steps[1]?.map((box) => box.problem)).toEqual(["not_resolved", "absent"]);
    expect(unresolved.steps.length).toBe(2);
  });

  it("zeigt Linie, Betreiber und Produktkategorie, nur wenn sie vorkommen", () => {
    const category = {
      role: "journey",
      ref: JOURNEY_VIEW.journey,
      target: JOURNEY_VIEW.journey as ObjectInfo,
      problem: null,
      shortName: { status: "found" as const, text: "RE", element: JOURNEY_VIEW.journey },
      names: [],
      master: null,
    };
    const master = row({ ...JOURNEY_VIEW, categories: [category] }, "master");
    expect(master.steps[1]?.map((box) => box.netex)).toEqual([
      "Line",
      "Operator",
      "TypeOfProductCategory",
    ]);
    const bare = row(
      { ...JOURNEY_VIEW, operator: ABSENT, line: ABSENT, transports: [], categories: [] },
      "master",
    );
    expect(names(bare)).toEqual([["ServiceJourney"]]);
  });

  it("nimmt das Line-Objekt der Linie und meldet eine nicht aufgelöste Kategorie", () => {
    const owner = JOURNEY_VIEW.stops[0]?.point as ObjectInfo;
    const transports = [
      ...JOURNEY_VIEW.transports,
      {
        ...(JOURNEY_VIEW.transports[0] as (typeof JOURNEY_VIEW.transports)[0]),
        owner,
        role: "line",
      },
    ];
    const broken = {
      role: "line",
      ref: JOURNEY_VIEW.journey,
      target: null,
      problem: { status: "not_resolved" as const, text: "c-x", element: null },
      shortName: ABSENT,
      names: [],
      master: null,
    };
    const master = row({ ...JOURNEY_VIEW, transports, categories: [broken] }, "master");
    expect(master.steps[1]?.[0]?.object?.id).toBe(owner.id);
    expect(master.steps[1]?.find((box) => box.netex === "TypeOfProductCategory")?.problem).toBe(
      "not_resolved",
    );
    const unresolvedLine = row(
      {
        ...JOURNEY_VIEW,
        line: { status: "not_resolved", text: "l-x", element: null },
        transports: [],
      },
      "master",
    );
    expect(unresolvedLine.steps[1]?.[0]).toMatchObject({ netex: "Line", problem: "not_resolved" });
  });
});

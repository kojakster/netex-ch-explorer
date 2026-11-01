// Aufbau-Übersicht einer Fahrt: welche Objekte die Fahrtansicht verbindet (reine Logik, ohne React).
// Es erscheint nur, was in den Daten vorkommt; nicht Aufgelöstes wird als solches gekennzeichnet.

import type {
  JourneyViewInfo,
  LookupStatus,
  ObjectInfo,
  StepKind,
  TimeInfo,
  ValueInfo,
} from "./types";

export type StructureRowId = "stops" | "times" | "days" | "master";

export const STRUCTURE_ROWS: readonly StructureRowId[] = ["stops", "times", "days", "master"];

export interface StructureText {
  key: string;
  params: Record<string, string | number>;
}

/** Eine Box der Übersicht: ein Objekt der Datei, eine Zusammenfassung oder ein Fehlendes. */
export interface StructureBox {
  /** Schlüssel für Listen; innerhalb einer Zeile eindeutig. */
  id: string;
  /** NeTEx-Name, unverändert; `null` bei abgeleiteten Angaben (z. B. berechnete Zeiten). */
  netex: string | null;
  /** Wert aus der Datei (ID oder Name). */
  detail: string | null;
  /** Zusammenfassung mit Zahl, übersetzt. */
  text: StructureText | null;
  /** Quelle in der Datei: bestimmt Farbe und Klickziel; `null`, wenn es keine gibt. */
  object: ObjectInfo | null;
  /** Gesetzt, wenn das Objekt fehlt oder sich nicht auflösen lässt. */
  problem: LookupStatus | null;
}

/** Schritte einer Zeile von links nach rechts; Boxen eines Schritts stehen untereinander. */
export interface StructureRow {
  id: StructureRowId;
  steps: StructureBox[][];
}

function present(value: ValueInfo): boolean {
  return value.status === "found";
}

function objectBox(
  id: string,
  netex: string,
  object: ObjectInfo,
  detail: string | null,
  text: StructureText | null = null,
): StructureBox {
  return { id, netex, detail, text, object, problem: null };
}

/** Fehlendes oder nicht Aufgelöstes; `reference` ist die gesuchte ID aus der Datei, falls bekannt. */
function missingBox(
  id: string,
  netex: string,
  problem: LookupStatus,
  reference: string | null = null,
): StructureBox {
  return { id, netex, detail: reference, text: null, object: null, problem };
}

function derivedBox(id: string, key: string, count: number): StructureBox {
  return {
    id,
    netex: null,
    detail: null,
    text: { key, params: { count } },
    object: null,
    problem: null,
  };
}

/** Box zu einer Angabe, die auf ein Objekt zeigt: gefunden, nicht aufgelöst oder (optional) fehlend. */
function lookupBox(
  id: string,
  netex: string,
  value: ValueInfo,
  options: { showAbsent: boolean },
): StructureBox | null {
  if (value.element !== null && present(value)) {
    return objectBox(id, netex, value.element, value.text);
  }
  if (value.status === "absent") {
    return options.showAbsent ? missingBox(id, netex, "absent") : null;
  }
  return missingBox(id, netex, value.status, value.text);
}

/**
 * Zusammenfassung gleichartiger Objekte aller Halte: eine Box mit Anzahl, die das erste Objekt
 * öffnet. Findet sich keines, steht der Grund des ersten Fehlenden da.
 */
function countBox(id: string, netex: string, values: readonly ValueInfo[]): StructureBox | null {
  const found = values.filter(present);
  const object = found.find((value) => value.element !== null)?.element ?? null;
  if (values.length === 0) {
    return null;
  }
  if (object === null) {
    const reason = values.find((value) => !present(value));
    return missingBox(id, netex, reason?.status ?? "absent", reason?.text ?? null);
  }
  const missing = values.length - found.length;
  const key = missing === 0 ? "structure.count" : "structure.countMissing";
  return {
    id,
    netex,
    detail: null,
    text: { key, params: { count: found.length, missing } },
    object,
    problem: null,
  };
}

function withoutNull(boxes: readonly (StructureBox | null)[]): StructureBox[] {
  return boxes.filter((box): box is StructureBox => box !== null);
}

function journeyBox(journey: JourneyViewInfo): StructureBox {
  return objectBox("journey", "ServiceJourney", journey.journey, journey.journey.xmlId);
}

function stopsRow(journey: JourneyViewInfo): StructureRow {
  const steps = [
    [journeyBox(journey)],
    withoutNull([
      lookupBox("pattern", "ServiceJourneyPattern", journey.pattern, { showAbsent: true }),
    ]),
  ];
  const stops = journey.stops;
  if (stops.length > 0 && present(journey.pattern)) {
    const assignments = stops.map(
      (stop): ValueInfo => ({
        status: stop.assignment === null ? "absent" : "found",
        text: null,
        element: stop.assignment,
      }),
    );
    steps.push(
      withoutNull([
        countBox(
          "points",
          "ScheduledStopPoint",
          stops.map((stop) => stop.stopPoint),
        ),
      ]),
      withoutNull([countBox("assignment", "PassengerStopAssignment", assignments)]),
      withoutNull([
        countBox(
          "quay",
          "Quay",
          stops.map((stop) => stop.quay),
        ),
        countBox(
          "place",
          "StopPlace",
          stops.map((stop) => stop.stopPlace),
        ),
      ]),
    );
  }
  return { id: "stops", steps: steps.filter((step) => step.length > 0) };
}

function distinctByKind(times: readonly TimeInfo[], kind: StepKind): ObjectInfo[] {
  const seen = new Map<string, ObjectInfo>();
  for (const time of times) {
    for (const step of time.chain) {
      if (step.kind === kind && !step.default && step.element !== null) {
        seen.set(step.element.id, step.element);
      }
    }
  }
  return [...seen.values()];
}

function timesRow(journey: JourneyViewInfo): StructureRow {
  const times = journey.stops.flatMap((stop) =>
    [stop.arrival, stop.departure].filter((time): time is TimeInfo => time !== null),
  );
  const steps: StructureBox[][] = [[journeyBox(journey)]];
  const demand = lookupBox("demand", "TimeDemandType", journey.timeDemandType, {
    showAbsent: false,
  });
  if (demand !== null) {
    steps.push([demand]);
  }
  const runTimes = distinctByKind(times, "run_time");
  const waitTimes = distinctByKind(times, "wait_time");
  const summands = [runTimes, waitTimes].flatMap((objects) => {
    const first = objects[0];
    return first === undefined
      ? []
      : [
          objectBox(first.name, first.name, first, null, {
            key: "structure.count",
            params: { count: objects.length, missing: 0 },
          }),
        ];
  });
  if (summands.length > 0) {
    steps.push(summands);
  }
  const explicit = times.filter((time) => time.status === "explicit").length;
  const computed = times.filter((time) => time.status === "computed").length;
  const failed = times.filter((time) => time.status === "not_computable").length;
  const results = [
    explicit > 0 ? derivedBox("explicit", "structure.times.explicit", explicit) : null,
    computed > 0 ? derivedBox("computed", "structure.times.computed", computed) : null,
    failed > 0 ? derivedBox("failed", "structure.times.failed", failed) : null,
  ].filter((box): box is StructureBox => box !== null);
  if (results.length > 0) {
    steps.push(results);
  }
  return { id: "times", steps };
}

function daysRow(journey: JourneyViewInfo): StructureRow {
  const steps: StructureBox[][] = [[journeyBox(journey)]];
  if (journey.validities.length === 0) {
    steps.push([missingBox("condition", "AvailabilityCondition", "absent")]);
    return { id: "days", steps };
  }
  const conditions: StructureBox[] = [];
  const bits: StructureBox[] = [];
  for (const [position, validity] of journey.validities.entries()) {
    const days = validity.days;
    if (days === null) {
      conditions.push(
        missingBox(
          `condition${position}`,
          "AvailabilityCondition",
          validity.problem?.status ?? "absent",
          validity.problem?.text ?? null,
        ),
      );
      continue;
    }
    conditions.push(
      objectBox(
        `condition${position}`,
        "AvailabilityCondition",
        days.condition,
        days.condition.xmlId,
      ),
    );
    bits.push(
      objectBox(
        `bits${position}`,
        days.validDayBits?.name ?? "ValidDayBits",
        days.validDayBits ?? days.condition,
        null,
        { key: "structure.days.count", params: { count: days.validCount ?? "?" } },
      ),
    );
  }
  steps.push(conditions);
  if (bits.length > 0) {
    steps.push(bits);
  }
  return { id: "days", steps };
}

function masterRow(journey: JourneyViewInfo): StructureRow {
  const line = journey.transports.find((transport) => transport.role === "line")?.owner ?? null;
  const boxes: (StructureBox | null)[] = [
    line === null
      ? lookupBox("line", "Line", journey.line, { showAbsent: false })
      : objectBox("line", "Line", line, journey.line.text),
    lookupBox("operator", "Operator", journey.operator, { showAbsent: false }),
    ...journey.categories.map((category) =>
      category.target === null
        ? missingBox(
            `category-${category.role}`,
            "TypeOfProductCategory",
            category.problem?.status ?? "absent",
            category.problem?.text ?? null,
          )
        : objectBox(
            `category-${category.role}`,
            "TypeOfProductCategory",
            category.target,
            category.shortName.text,
          ),
    ),
  ];
  return {
    id: "master",
    steps: [[journeyBox(journey)], boxes.filter((box): box is StructureBox => box !== null)].filter(
      (step) => step.length > 0,
    ),
  };
}

/** Die Zeilen der Aufbau-Übersicht: Halte, Zeiten, Betriebstage, Stammdaten. */
export function buildStructure(journey: JourneyViewInfo): StructureRow[] {
  return [stopsRow(journey), timesRow(journey), daysRow(journey), masterRow(journey)];
}

// Gemeinsame Testdaten für die Vitest-Tests (synthetisch).

import type { DataSource } from "./api";
import type {
  AppInfo,
  ChainLink,
  DatasetInfo,
  GuideInfo,
  JourneyInfo,
  JourneyViewInfo,
  ObjectDetail,
  ObjectInfo,
  ObjectTreeResult,
  ReferenceInfo,
  StepInfo,
  StopInfo,
  TimeInfo,
  ValueInfo,
  XmlWindow,
} from "./types";

export const APP_INFO: AppInfo = {
  language: "de-CH",
  languages: ["de-CH", "en"],
  frameColors: [
    { key: "TimetableFrame", background: "#0057B8", text: "#FFFFFF" },
    { key: "notRelevant", background: "#8A8A8A", text: "#000000" },
  ],
  notRelevantElements: ["SiteFacilitySet", "TariffZone"],
  features: ["guide_status", "help_page"],
  checks: [
    { id: "xsd", status: "performed", sources: ["xsd/xsd/NeTEx_publication.xsd"] },
    { id: "ch_profile_rules", status: "deferred", sources: [] },
  ],
  coreRules: [
    {
      id: "CH-SJ-13",
      kind: "forbidden",
      severity: "error",
      context: "ServiceJourney",
      targets: ["calls"],
      source: "templates/ServiceJourney.xml Z. 145-153",
      allowed: [],
    },
    {
      id: "CH-SJ-03",
      kind: "value",
      severity: "error",
      context: "ServiceJourney",
      targets: ["ServiceAlteration"],
      source: "templates/ServiceJourney.xml Z. 89-91",
      allowed: ["planned"],
    },
  ],
  severities: ["error", "warning", "info"],
  issues: [],
};

export const GUIDE: GuideInfo = {
  path: "/synthetic/netexRealisationGuideSwitzerland",
  found: true,
  branch: "next",
  commit: "b7ac15860369818a8fb53c64ed6f71318f019380",
  xsdCommit: "73b337e22ceed7905a1be14e4e506f1afa359b54",
  xsdPresent: true,
  testState: "tested",
  testedCommit: "b7ac15860369818a8fb53c64ed6f71318f019380",
  mappingSheets: [{ name: "StopUse", headerRow: 3, rows: 4 }],
  examples: [
    {
      name: "ch20_three_stops.xml",
      title: "Synthetische Fahrt",
      result: "clean",
      counts: {},
      change: "unchanged",
    },
    {
      name: "broken_xml.xml",
      title: null,
      result: "unreadable",
      counts: { error: 1 },
      change: "new",
    },
  ],
  examplesReady: true,
  xsdLoaded: true,
  issues: [],
};

export const JOURNEY_OBJECT: ObjectInfo = {
  id: "SYNTHETICDATASET01.100",
  name: "ServiceJourney",
  xmlId: "ch:1:sjyid:SYN:1",
  version: "1",
  label: null,
  fileName: "ch20_three_stops.xml",
  line: 151,
  column: 7,
  frame: {
    objectId: "SYNTHETICDATASET01.90",
    name: "TimetableFrame",
    xmlId: "ch:1:TimetableFrame:SYN",
  },
  colorKey: "TimetableFrame",
  notRelevant: false,
};

export const TARGET_OBJECT: ObjectInfo = {
  id: "SYNTHETICDATASET01.60",
  name: "Operator",
  xmlId: "ch:1:sboid:SYN1",
  version: "1",
  label: "Synthetischer Betreiber",
  fileName: "ch20_three_stops.xml",
  line: 30,
  column: 7,
  frame: JOURNEY_OBJECT.frame,
  colorKey: "TimetableFrame",
  notRelevant: false,
};

const OPERATOR_REF_ELEMENT: ObjectInfo = {
  ...TARGET_OBJECT,
  id: "SYNTHETICDATASET01.106",
  name: "OperatorRef",
  xmlId: null,
  label: null,
  line: 158,
};

/** Verweis des Fahrt-Objekts auf den Betreiber (aufgelöst). */
export const OUTGOING_REFERENCE: ReferenceInfo = {
  element: OPERATOR_REF_ELEMENT,
  ref: "ch:1:sboid:SYN1",
  refVersion: "1",
  status: "resolved",
  expected: ["Operator"],
  target: TARGET_OBJECT,
  owner: JOURNEY_OBJECT,
};

/** Verweis, der ins Leere zeigt: Objekte des Typs sind vorhanden, die ID fehlt. */
export const UNRESOLVED_REFERENCE: ReferenceInfo = {
  element: { ...OPERATOR_REF_ELEMENT, id: "SYNTHETICDATASET01.107", name: "LineRef" },
  ref: "ch:1:slnid:SYN9",
  refVersion: "1",
  status: "unresolved",
  expected: ["Line"],
  target: null,
  owner: JOURNEY_OBJECT,
};

export const DATASET: DatasetInfo = {
  id: "SYNTHETICDATASET01",
  files: [
    {
      id: 1,
      name: "ch20_three_stops.xml",
      size: 7504,
      sha256: "0".repeat(64),
      readable: true,
      elements: 113,
      objects: 30,
      detection: {
        status: "detected",
        profile: "ch_2_0",
        reasons: [
          {
            evidence: "ch_2_0",
            key: "version.attribute_20",
            params: { version: "2.1" },
          },
          { evidence: "ch_2_0", key: "version.structure_pattern", params: {} },
        ],
      },
    },
  ],
  objectTypes: [{ name: "ServiceJourney", count: 1 }],
  frames: [],
  diagnosticCounts: { error: 0, warning: 0, info: 0 },
  validation: null,
};

/** Ergebnis einer Validierung des Beispiel-Datensatzes. */
export const VALIDATED_DATASET: DatasetInfo = {
  ...DATASET,
  diagnosticCounts: { error: 1, warning: 0, info: 0 },
  validation: {
    guideCommit: GUIDE.commit,
    forced: false,
    steps: [
      { id: "xsd", performed: true, reason: null },
      { id: "general_rules", performed: true, reason: null },
      { id: "ch_core_rules", performed: true, reason: null },
    ],
    files: [{ fileId: 1, checked: true, reason: null, forced: false }],
  },
};

export const JOURNEYS: JourneyInfo[] = [
  {
    object: JOURNEY_OBJECT,
    trainNumbers: [{ status: "found", text: "1", objectId: "SYNTHETICDATASET01.110" }],
    departureTime: { status: "found", text: "08:00:00", objectId: "SYNTHETICDATASET01.104" },
    departureDayOffset: { status: "found", text: "0", objectId: "SYNTHETICDATASET01.105" },
    line: { status: "found", text: "Synthetische Linie", objectId: "SYNTHETICDATASET01.40" },
    firstStop: { status: "found", text: "Synthetisch A", objectId: "SYNTHETICDATASET01.50" },
    lastStop: {
      status: "not_resolved",
      text: "ch:1:sloid:SYN9:0:1",
      objectId: "SYNTHETICDATASET01.80",
    },
    category: { status: "found", text: "SYN", objectId: "SYNTHETICDATASET01.41" },
  },
];

export const DETAIL: ObjectDetail = {
  object: JOURNEY_OBJECT,
  path: "/PublicationDelivery/dataObjects/CompositeFrame/frames/TimetableFrame/vehicleJourneys/ServiceJourney",
  attributes: { id: "ch:1:sjyid:SYN:1", version: "1" },
  properties: [
    {
      id: "SYNTHETICDATASET01.104",
      name: "DepartureTime",
      attributes: {},
      text: "08:00:00",
      line: 156,
      column: 8,
      reference: null,
      children: [],
    },
    {
      id: "SYNTHETICDATASET01.106",
      name: "OperatorRef",
      attributes: { ref: "ch:1:sboid:SYN1", version: "1" },
      text: "",
      line: 158,
      column: 8,
      reference: { status: "resolved", targetId: "SYNTHETICDATASET01.60", expected: ["Operator"] },
      children: [],
    },
  ],
  truncated: false,
  reference: null,
  outgoing: [OUTGOING_REFERENCE, UNRESOLVED_REFERENCE],
  incoming: [],
  referencesTruncated: false,
};

/** Der Betreiber: wird von der Fahrt verwiesen (eingehender Verweis). */
export const TARGET_DETAIL: ObjectDetail = {
  object: TARGET_OBJECT,
  path: "/PublicationDelivery/dataObjects/CompositeFrame/frames/TimetableFrame/Operator",
  attributes: { id: "ch:1:sboid:SYN1", version: "1" },
  properties: [],
  truncated: false,
  reference: null,
  outgoing: [],
  incoming: [OUTGOING_REFERENCE],
  referencesTruncated: false,
};

export const PROVENANCE: ChainLink[] = [
  {
    kind: "frame",
    object: { ...JOURNEY_OBJECT, id: "SYNTHETICDATASET01.90", name: "TimetableFrame" },
  },
  { kind: "object", object: JOURNEY_OBJECT },
  { kind: "element", object: OPERATOR_REF_ELEMENT },
  { kind: "target", object: TARGET_OBJECT },
];

export const XML: XmlWindow = {
  fileName: "ch20_three_stops.xml",
  firstLine: 150,
  text: '<vehicleJourneys>\n<ServiceJourney id="ch:1:sjyid:SYN:1">\n<DepartureTime>08:00:00</DepartureTime>\n</ServiceJourney>',
  focusFrom: 18,
  focusTo: 117,
  frames: [
    {
      objectId: "SYNTHETICDATASET01.90",
      name: "TimetableFrame",
      xmlId: "ch:1:TimetableFrame:SYN",
      colorKey: "TimetableFrame",
      fromLine: 150,
      toLine: 153,
    },
  ],
  truncated: false,
};

function element(
  id: number,
  name: string,
  colorKey: string,
  xmlId: string | null = null,
): ObjectInfo {
  return {
    id: `SYNTHETICDATASET01.${id}`,
    name,
    xmlId,
    version: null,
    label: null,
    fileName: "ch20_three_stops.xml",
    line: id,
    column: 8,
    frame: { objectId: "SYNTHETICDATASET01.90", name: colorKey, xmlId: `ch:1:${colorKey}:SYN` },
    colorKey,
    notRelevant: false,
  };
}

function found(source: ObjectInfo, text: string): ValueInfo {
  return { status: "found", text, element: source };
}

const ABSENT_VALUE: ValueInfo = { status: "absent", text: null, element: null };

function stopInfo(
  position: number,
  name: string,
  arrival: TimeInfo | null,
  departure: TimeInfo | null,
): StopInfo {
  const base = 200 + position * 10;
  return {
    position,
    point: element(base, "StopPointInJourneyPattern", "ServiceFrame", `spijp${position}`),
    stopPoint: found(element(base + 1, "Name", "ServiceFrame"), name),
    stopPlace: found(element(base + 2, "Name", "SiteFrame"), `Haltestelle ${name}`),
    quay: found(element(base + 3, "PublicCode", "SiteFrame"), String(position)),
    assignment: element(base + 4, "PassengerStopAssignment", "ServiceFrame", `psa${position}`),
    forBoarding: found(
      element(base + 5, "ForBoarding", "ServiceFrame"),
      position === 3 ? "false" : "true",
    ),
    forAlighting: found(
      element(base + 6, "ForAlighting", "ServiceFrame"),
      position === 1 ? "false" : "true",
    ),
    requestStop: ABSENT_VALUE,
    stopUse: null,
    arrival,
    departure,
    partNumbers: position === 1 ? [1] : [],
  };
}

function timeInfo(
  id: string,
  clock: string,
  status: "explicit" | "computed",
  chain: StepInfo[],
): TimeInfo {
  return {
    id,
    status,
    clock,
    dayOffset: 0,
    offsetOrigin: "explicit",
    source: chain[chain.length - 1]?.element ?? null,
    chain,
    reason: null,
  };
}

const DEPARTURE_STEP: StepInfo = {
  kind: "departure_time",
  value: "08:00:00",
  default: false,
  seconds: 28800,
  clock: "08:00:00",
  dayOffset: 0,
  element: element(104, "DepartureTime", "TimetableFrame"),
  related: [],
  viaFromTo: false,
};

const RUN_STEP: StepInfo = {
  kind: "run_time",
  value: "PT10M",
  default: false,
  seconds: 600,
  clock: "08:10:00",
  dayOffset: 0,
  element: element(130, "RunTime", "ServiceFrame"),
  related: [element(120, "TimingLink", "ServiceFrame", "tl-1")],
  viaFromTo: true,
};

const WAIT_DEFAULT_STEP: StepInfo = {
  kind: "wait_time",
  value: null,
  default: true,
  seconds: 0,
  clock: "08:10:00",
  dayOffset: 0,
  element: null,
  related: [],
  viaFromTo: false,
};

const NOT_COMPUTABLE: TimeInfo = {
  id: "arrival-3",
  status: "not_computable",
  clock: null,
  dayOffset: 0,
  offsetOrigin: null,
  source: null,
  chain: [],
  reason: {
    severity: "warning",
    key: "projection.time.run_time_missing",
    params: { link: "tl-2" },
    element: element(121, "TimingLink", "ServiceFrame", "tl-2"),
  },
};

/** Fahrtansicht der synthetischen Fahrt: zweiter Halt berechnet, dritte Ankunft nicht berechenbar. */
export const JOURNEY_VIEW: JourneyViewInfo = {
  journey: JOURNEY_OBJECT,
  guideCommit: "b7ac15860369818a8fb53c64ed6f71318f019380",
  pattern: found(
    element(140, "ServiceJourneyPattern", "ServiceFrame", "ch:1:SJP:SYN"),
    "ch:1:SJP:SYN",
  ),
  timeDemandType: found(element(141, "TimeDemandType", "ServiceFrame", "tdt"), "tdt"),
  operator: found(element(142, "Name", "ResourceFrame"), "Synthetische Bahn"),
  trainNumbers: [found(element(110, "ForAdvertisement", "TimetableFrame"), "1")],
  privateCodes: [],
  line: found(element(40, "PublicCode", "ServiceFrame"), "Synthetische Linie"),
  transports: [
    {
      owner: JOURNEY_OBJECT,
      role: "journey",
      mode: found(element(107, "TransportMode", "TimetableFrame"), "rail"),
      submodeType: null,
      submode: ABSENT_VALUE,
    },
  ],
  categories: [],
  validities: [
    {
      ref: element(108, "AvailabilityConditionRef", "TimetableFrame"),
      days: {
        condition: element(150, "AvailabilityCondition", "ServiceCalendarFrame", "ch:1:AC:SYN"),
        fromDate: element(151, "FromDate", "ServiceCalendarFrame"),
        toDate: element(152, "ToDate", "ServiceCalendarFrame"),
        validDayBits: element(153, "ValidDayBits", "ServiceCalendarFrame"),
        firstDay: "2026-12-13",
        lastDay: "2026-12-19",
        periodDays: 7,
        validCount: 5,
        days: ["2026-12-14", "2026-12-15"],
        daysListed: true,
        findings: [],
      },
      problem: null,
    },
  ],
  stops: [
    stopInfo(
      1,
      "Synthetisch A",
      null,
      timeInfo("departure-1", "08:00:00", "explicit", [DEPARTURE_STEP]),
    ),
    stopInfo(
      2,
      "Synthetisch B",
      timeInfo("arrival-2", "08:10:00", "computed", [DEPARTURE_STEP, RUN_STEP]),
      timeInfo("departure-2", "08:10:00", "computed", [
        DEPARTURE_STEP,
        RUN_STEP,
        WAIT_DEFAULT_STEP,
      ]),
    ),
    stopInfo(3, "Synthetisch C", NOT_COMPUTABLE, null),
  ],
  parts: [
    {
      number: 1,
      element: element(160, "JourneyPart", "TimetableFrame", "jp1"),
      description: [],
      purpose: found(element(161, "Name", "ResourceFrame"), "Facility change"),
      trainNumbers: [],
      parentJourney: ABSENT_VALUE,
      startStop: {
        stop: found(element(162, "Name", "ServiceFrame"), "Synthetisch A"),
        position: 1,
      },
      endStop: { stop: found(element(163, "Name", "ServiceFrame"), "Synthetisch B"), position: 2 },
      start: {
        time: found(element(164, "StartTime", "TimetableFrame"), "08:00:00"),
        dayOffset: ABSENT_VALUE,
        clock: "08:00:00",
        day: 0,
      },
      end: {
        time: found(element(165, "EndTime", "TimetableFrame"), "08:10:00"),
        dayOffset: ABSENT_VALUE,
        clock: "08:10:00",
        day: 0,
      },
      facilities: [
        {
          ref: element(166, "ServiceFacilitySetRef", "TimetableFrame"),
          facilitySet: element(167, "ServiceFacilitySet", "ResourceFrame", "fs-bistro"),
          problem: null,
          description: [],
          groups: [
            {
              element: element(168, "CateringFacilityList", "ResourceFrame"),
              codes: [
                {
                  code: "bistro",
                  element: element(168, "CateringFacilityList", "ResourceFrame"),
                  master: {
                    status: "found",
                    matches: [
                      {
                        sheet: "Angebote",
                        row: 103,
                        texts: [
                          { label: "Angebotabkürzung", text: "WS" },
                          { label: "Angebottext", text: "Bistro" },
                        ],
                      },
                    ],
                  },
                },
              ],
            },
          ],
        },
      ],
      validity: [],
      category: null,
    },
  ],
  facilities: [],
  notices: [
    {
      assignment: element(170, "NoticeAssignment", "TimetableFrame", "na1"),
      scope: "journey",
      ref: element(171, "NoticeRef", "TimetableFrame"),
      notice: element(172, "Notice", "ServiceFrame", "ch:1:Notice:SYN"),
      problem: null,
      shortCode: found(element(173, "ShortCode", "ServiceFrame"), "SYN1"),
      noticeType: ABSENT_VALUE,
      texts: [
        {
          text: {
            lang: "de",
            text: "Synthetischer Hinweis",
            element: element(174, "Text", "ServiceFrame"),
          },
          alternativeFor: null,
        },
        {
          text: {
            lang: "en",
            text: "Synthetic notice",
            element: element(175, "Text", "ServiceFrame"),
          },
          alternativeFor: null,
        },
      ],
      startRef: null,
      endRef: null,
      startPosition: null,
      endPosition: null,
      validity: [],
    },
  ],
  diagnostics: [
    {
      category: "projection",
      severity: "warning",
      key: "projection.time.run_time_missing",
      params: { link: "tl-2" },
      fileId: 1,
      fileName: "ch20_three_stops.xml",
      line: 121,
      column: 8,
      guideLink: null,
    },
  ],
};

function treeObject(id: number, name: string, xmlId: string, colorKey: string | null): ObjectInfo {
  return {
    ...JOURNEY_OBJECT,
    id: `SYNTHETICDATASET01.${id}`,
    name,
    xmlId,
    label: null,
    colorKey,
    notRelevant: colorKey === "notRelevant",
  };
}

/** Objektliste: ein Frame mit Objekt und Unterobjekt, ein Frame ohne Inhalt, ein Objekt ausserhalb. */
export const OBJECT_TREE: ObjectTreeResult = {
  entries: [
    {
      object: treeObject(1, "TimetableFrame", "ch:1:TimetableFrame:SYN", "TimetableFrame"),
      isFrame: true,
      depth: 0,
      matches: true,
    },
    {
      object: {
        ...treeObject(2, "StopPlace", "ch:1:sloid:SYN1", "TimetableFrame"),
        label: "Spiez",
      },
      isFrame: false,
      depth: 1,
      matches: true,
    },
    {
      object: treeObject(3, "Quay", "ch:1:sloid:SYN1:0:8", "TimetableFrame"),
      isFrame: false,
      depth: 2,
      matches: false,
    },
    {
      object: treeObject(4, "SiteFacilitySet", "ch:1:sfs:SYN", "notRelevant"),
      isFrame: false,
      depth: 1,
      matches: true,
    },
  ],
  outside: [
    {
      object: treeObject(5, "Loose", "ch:1:loose", null),
      isFrame: false,
      depth: 0,
      matches: true,
    },
  ],
  total: 5,
  shown: 5,
  truncated: false,
};

/** Synthetische Datenquelle; einzelne Aufrufe lassen sich ersetzen. */
export function fakeSource(overrides: Partial<DataSource> = {}): DataSource {
  return {
    getAppInfo: () => Promise.resolve(APP_INFO),
    getGuide: () => Promise.resolve(GUIDE),
    openExample: () => Promise.resolve(DATASET),
    openFiles: () => Promise.resolve(DATASET),
    validate: () => Promise.resolve(VALIDATED_DATASET),
    closeDataset: () => Promise.resolve(),
    getJourneys: () => Promise.resolve(JOURNEYS),
    getJourney: () => Promise.resolve(JOURNEY_VIEW),
    getObjectTree: () => Promise.resolve(OBJECT_TREE),
    getDiagnostics: () => Promise.resolve([]),
    getObject: (id) => Promise.resolve(id === TARGET_OBJECT.id ? TARGET_DETAIL : DETAIL),
    getObjectXml: () => Promise.resolve(XML),
    getProvenance: () => Promise.resolve(PROVENANCE),
    getXmlAt: () => Promise.resolve(XML),
    ...overrides,
  };
}

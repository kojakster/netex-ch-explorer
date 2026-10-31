// Gemeinsame Testdaten für die Vitest-Tests (synthetisch).

import type { DataSource } from "./api";
import type {
  AppInfo,
  ChainLink,
  DatasetInfo,
  GuideInfo,
  JourneyInfo,
  ObjectDetail,
  ObjectInfo,
  ReferenceInfo,
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
    },
  ],
  objectTypes: [{ name: "ServiceJourney", count: 1 }],
  frames: [],
  diagnosticCounts: { error: 0, warning: 0, info: 0 },
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

/** Synthetische Datenquelle; einzelne Aufrufe lassen sich ersetzen. */
export function fakeSource(overrides: Partial<DataSource> = {}): DataSource {
  return {
    getAppInfo: () => Promise.resolve(APP_INFO),
    getGuide: () => Promise.resolve(GUIDE),
    openExample: () => Promise.resolve(DATASET),
    getJourneys: () => Promise.resolve(JOURNEYS),
    searchObjects: () => Promise.resolve({ total: 1, items: [JOURNEY_OBJECT] }),
    getDiagnostics: () => Promise.resolve([]),
    getObject: (id) => Promise.resolve(id === TARGET_OBJECT.id ? TARGET_DETAIL : DETAIL),
    getObjectXml: () => Promise.resolve(XML),
    getProvenance: () => Promise.resolve(PROVENANCE),
    getXmlAt: () => Promise.resolve(XML),
    ...overrides,
  };
}

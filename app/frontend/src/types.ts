// Antworttypen der lokalen Schnittstelle (Vertrag: docs/api.md).

export type Severity = "error" | "warning" | "info";
export type GuideTestState = "tested" | "differs" | "never_tested" | "unknown";
export type CheckStatus = "performed" | "not_implemented" | "deferred";

export interface Issue {
  severity: Severity;
  key: string;
  params: Record<string, string | number>;
}

export interface MappingSheet {
  name: string;
  headerRow: number;
  rows: number;
}

export interface GuideInfo {
  path: string;
  found: boolean;
  branch: string | null;
  commit: string | null;
  xsdCommit: string | null;
  xsdPresent: boolean;
  testState: GuideTestState;
  testedCommit: string | null;
  mappingSheets: MappingSheet[];
  examples: ExampleInfo[];
  issues: Issue[];
}

export interface FrameColor {
  key: string;
  background: string;
  text: string;
}

export interface CheckStep {
  id: string;
  status: CheckStatus;
  sources: string[];
}

export interface AppInfo {
  language: string;
  languages: string[];
  frameColors: FrameColor[];
  notRelevantElements: string[];
  features: string[];
  checks: CheckStep[];
  severities: Severity[];
  issues: Issue[];
}

export type ExampleResult = "clean" | "notes" | "errors" | "unreadable";
export type ExampleChange = "unchanged" | "changed" | "new" | "untested";

export interface ExampleInfo {
  name: string;
  title: string | null;
  result: ExampleResult;
  counts: Partial<Record<Severity, number>>;
  change: ExampleChange;
}

export interface FileInfo {
  id: number;
  name: string;
  size: number;
  sha256: string;
  readable: boolean;
  elements: number;
  objects: number;
}

export interface FrameRef {
  objectId: string;
  name: string;
  xmlId: string | null;
}

export interface ObjectInfo {
  id: string;
  name: string;
  xmlId: string | null;
  version: string | null;
  label: string | null;
  fileName: string;
  line: number;
  column: number;
  frame: FrameRef | null;
  colorKey: string | null;
  notRelevant: boolean;
}

export interface DatasetInfo {
  id: string;
  files: FileInfo[];
  objectTypes: { name: string; count: number }[];
  frames: ObjectInfo[];
  diagnosticCounts: Record<Severity, number>;
}

export interface ObjectSearchResult {
  total: number;
  items: ObjectInfo[];
}

export type ReferenceStatus = "resolved" | "unresolved" | "ambiguous" | "external_or_unloaded";

export interface PropertyReference {
  status: ReferenceStatus;
  targetId: string | null;
  expected: string[];
}

export interface PropertyInfo {
  id: string;
  name: string;
  attributes: Record<string, string>;
  text: string;
  line: number;
  column: number;
  reference: PropertyReference | null;
  children: PropertyInfo[];
}

export interface ReferenceInfo {
  element: ObjectInfo;
  ref: string;
  refVersion: string | null;
  status: ReferenceStatus;
  expected: string[];
  target: ObjectInfo | null;
  owner: ObjectInfo | null;
}

export type ChainKind = "frame" | "object" | "element" | "target";

export interface ChainLink {
  kind: ChainKind;
  object: ObjectInfo;
}

export interface ObjectDetail {
  object: ObjectInfo;
  path: string;
  attributes: Record<string, string>;
  properties: PropertyInfo[];
  truncated: boolean;
  reference: ReferenceInfo | null;
  outgoing: ReferenceInfo[];
  incoming: ReferenceInfo[];
  referencesTruncated: boolean;
}

export type LookupStatus =
  | "found"
  | "absent"
  | "not_resolved"
  | "ambiguous"
  | "external_or_unloaded";

export interface LookupInfo {
  status: LookupStatus;
  text: string | null;
  objectId: string | null;
}

export interface JourneyInfo {
  object: ObjectInfo;
  trainNumbers: LookupInfo[];
  departureTime: LookupInfo;
  departureDayOffset: LookupInfo;
  line: LookupInfo;
  firstStop: LookupInfo;
  lastStop: LookupInfo;
}

export interface DiagnosticInfo {
  category: string;
  severity: Severity;
  key: string;
  params: Record<string, string | number>;
  fileId: number;
  fileName: string;
  line: number | null;
  column: number | null;
}

export interface FrameBand {
  objectId: string;
  name: string;
  xmlId: string | null;
  colorKey: string | null;
  fromLine: number;
  toLine: number;
}

export interface XmlWindow {
  fileName: string;
  firstLine: number;
  text: string;
  focusFrom: number;
  focusTo: number;
  frames: FrameBand[];
  truncated: boolean;
}

export interface SearchParams {
  type?: string;
  q?: string;
  limit: number;
  offset: number;
}

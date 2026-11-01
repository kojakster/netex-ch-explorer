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
  /** `false`, solange die Beispiele noch geprüft werden (die XSD wird geladen). */
  examplesReady: boolean;
  xsdLoaded: boolean;
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

export type RuleKind = "required" | "exactly_one" | "forbidden" | "value" | "expected";

export interface CoreRule {
  id: string;
  kind: RuleKind;
  severity: Severity;
  context: string;
  targets: string[];
  source: string;
  allowed: string[];
}

export interface AppInfo {
  language: string;
  languages: string[];
  frameColors: FrameColor[];
  notRelevantElements: string[];
  features: string[];
  checks: CheckStep[];
  coreRules: CoreRule[];
  severities: Severity[];
  issues: Issue[];
}

export type ExampleResult = "clean" | "notes" | "errors" | "unreadable" | "check_failed";
export type ExampleChange = "unchanged" | "changed" | "new" | "untested";

export interface ExampleInfo {
  name: string;
  title: string | null;
  /** `null`, solange die Beispiele noch geprüft werden. */
  result: ExampleResult | null;
  counts: Partial<Record<Severity, number>>;
  change: ExampleChange;
}

export type DetectionStatus = "detected" | "ambiguous" | "unknown";
export type ProfileVersion = "ch_2_0" | "netex_1_10";
export type Evidence = "ch_2_0" | "netex_1_10" | "neutral";

export interface DetectionReason {
  evidence: Evidence;
  key: string;
  params: Record<string, string | number>;
}

export interface Detection {
  status: DetectionStatus;
  profile: ProfileVersion | null;
  reasons: DetectionReason[];
}

export interface FileInfo {
  id: number;
  name: string;
  size: number;
  sha256: string;
  readable: boolean;
  elements: number;
  objects: number;
  detection: Detection | null;
}

export interface ValidationStep {
  id: string;
  performed: boolean;
  reason: Issue | null;
}

export interface ValidationFile {
  fileId: number;
  checked: boolean;
  reason: Issue | null;
  /** Auf Wunsch als CH 2.0 geprüft, obwohl die Version nicht erkannt war. */
  forced: boolean;
}

/** Ergebnis einer Validierung: „geprüft gegen Entwurf <Commit>“, nie „gültig“. */
export interface ValidationInfo {
  guideCommit: string | null;
  forced: boolean;
  steps: ValidationStep[];
  files: ValidationFile[];
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
  validation: ValidationInfo | null;
}

/** Ein Eintrag der Objektliste: Frame (Kopfzeile) oder Objekt, mit Einrückungsebene. */
export interface ObjectTreeEntry {
  object: ObjectInfo;
  isFrame: boolean;
  depth: number;
  /** `false` bei Vorfahren, die bei aktivem Filter nur den Zusammenhang zeigen. */
  matches: boolean;
}

export interface ObjectTreeResult {
  /** Frames mit ihren Objekten in Vorordnung. */
  entries: ObjectTreeEntry[];
  /** Objekte ausserhalb jedes Frames in Vorordnung. */
  outside: ObjectTreeEntry[];
  total: number;
  shown: number;
  truncated: boolean;
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
  /** `ShortName` der Produktkategorie der Fahrt (Abzeichen in der Liste). */
  category: LookupInfo;
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
  guideLink: string | null;
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
}

// Fahrtansicht (`GET /api/journeys/{id}`)

export interface ValueInfo {
  status: LookupStatus;
  text: string | null;
  element: ObjectInfo | null;
}

export interface LangTextInfo {
  lang: string | null;
  text: string;
  element: ObjectInfo;
}

export interface MasterMatchInfo {
  sheet: string;
  row: number;
  texts: { label: string; text: string }[];
}

export type MasterStatus = "found" | "none" | "unavailable";

export interface MasterInfo {
  status: MasterStatus;
  matches: MasterMatchInfo[];
}

export interface CodeInfo {
  code: string;
  element: ObjectInfo;
  master: MasterInfo | null;
}

export interface FindingInfo {
  severity: Severity;
  key: string;
  params: Record<string, string | number>;
  element: ObjectInfo | null;
}

export type StepKind = "departure_time" | "day_offset" | "run_time" | "wait_time";

export interface StepInfo {
  kind: StepKind;
  value: string | null;
  default: boolean;
  seconds: number;
  clock: string;
  dayOffset: number;
  element: ObjectInfo | null;
  related: ObjectInfo[];
  viaFromTo: boolean;
}

export type TimeStatus = "explicit" | "computed" | "not_computable";
export type OffsetOrigin = "explicit" | "default" | "computed";

export interface TimeInfo {
  id: string;
  status: TimeStatus;
  clock: string | null;
  dayOffset: number;
  offsetOrigin: OffsetOrigin | null;
  source: ObjectInfo | null;
  chain: StepInfo[];
  reason: FindingInfo | null;
}

export interface StopInfo {
  position: number;
  point: ObjectInfo;
  stopPoint: ValueInfo;
  stopPlace: ValueInfo;
  quay: ValueInfo;
  assignment: ObjectInfo | null;
  forBoarding: ValueInfo;
  forAlighting: ValueInfo;
  requestStop: ValueInfo;
  stopUse: CodeInfo | null;
  arrival: TimeInfo | null;
  departure: TimeInfo | null;
  partNumbers: number[];
}

export interface OperatingDaysInfo {
  condition: ObjectInfo;
  fromDate: ObjectInfo | null;
  toDate: ObjectInfo | null;
  validDayBits: ObjectInfo | null;
  firstDay: string | null;
  lastDay: string | null;
  periodDays: number | null;
  validCount: number | null;
  days: string[];
  daysListed: boolean;
  findings: FindingInfo[];
}

export interface ValidityInfo {
  ref: ObjectInfo;
  days: OperatingDaysInfo | null;
  problem: ValueInfo | null;
}

export interface FacilityGroupInfo {
  element: ObjectInfo;
  codes: CodeInfo[];
}

export interface FacilitySetInfo {
  ref: ObjectInfo;
  facilitySet: ObjectInfo | null;
  problem: ValueInfo | null;
  description: LangTextInfo[];
  groups: FacilityGroupInfo[];
}

export interface TransportInfo {
  owner: ObjectInfo;
  role: string;
  mode: ValueInfo;
  submodeType: string | null;
  submode: ValueInfo;
}

export interface CategoryInfo {
  role: string;
  ref: ObjectInfo;
  target: ObjectInfo | null;
  problem: ValueInfo | null;
  shortName: ValueInfo;
  names: LangTextInfo[];
  master: MasterInfo | null;
}

export interface PartTimeInfo {
  time: ValueInfo;
  dayOffset: ValueInfo;
  clock: string | null;
  day: number | null;
}

export interface PartBoundaryInfo {
  stop: ValueInfo;
  position: number | null;
}

export interface PartInfo {
  number: number;
  element: ObjectInfo;
  description: LangTextInfo[];
  purpose: ValueInfo;
  trainNumbers: ValueInfo[];
  parentJourney: ValueInfo;
  startStop: PartBoundaryInfo;
  endStop: PartBoundaryInfo;
  start: PartTimeInfo;
  end: PartTimeInfo;
  facilities: FacilitySetInfo[];
  validity: ValidityInfo[];
  category: CategoryInfo | null;
}

export type NoticeScope = "journey" | "pattern" | "journey_ref" | "pattern_ref" | "stop";

export interface NoticeInfo {
  assignment: ObjectInfo;
  scope: NoticeScope;
  ref: ObjectInfo | null;
  notice: ObjectInfo | null;
  problem: ValueInfo | null;
  shortCode: ValueInfo;
  noticeType: ValueInfo;
  texts: { text: LangTextInfo; alternativeFor: string | null }[];
  startRef: ObjectInfo | null;
  endRef: ObjectInfo | null;
  startPosition: number | null;
  endPosition: number | null;
  validity: ValidityInfo[];
}

export interface PrivateCodeInfo {
  codeType: string | null;
  value: string;
  element: ObjectInfo;
}

export interface JourneyViewInfo {
  journey: ObjectInfo;
  guideCommit: string | null;
  pattern: ValueInfo;
  timeDemandType: ValueInfo;
  /** Betreiber (`OperatorRef` der Fahrt) mit Name aus der Datei. */
  operator: ValueInfo;
  trainNumbers: ValueInfo[];
  privateCodes: PrivateCodeInfo[];
  line: ValueInfo;
  transports: TransportInfo[];
  categories: CategoryInfo[];
  validities: ValidityInfo[];
  stops: StopInfo[];
  parts: PartInfo[];
  facilities: FacilitySetInfo[];
  notices: NoticeInfo[];
  diagnostics: DiagnosticInfo[];
}

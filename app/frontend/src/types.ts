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

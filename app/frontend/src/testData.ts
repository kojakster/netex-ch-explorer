// Gemeinsame Testdaten für die Vitest-Tests (synthetisch).

import type { AppInfo, GuideInfo } from "./types";

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
  issues: [],
};

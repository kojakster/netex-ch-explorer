// Symbole der Schweregrade und Status (docs/decisions.md, „Symbol für Warnung“).
// Symbole sind sprachunabhängig; der zugehörige Text steht immer in den Sprachdateien.

import type { ReferenceStatus, Severity } from "./types";

export const SEVERITY_SYMBOLS: Readonly<Record<Severity, string>> = {
  error: "⚠",
  warning: "△",
  info: "ℹ",
};

export const OK_SYMBOL = "✔";
export const UNREADABLE_SYMBOL = "✖";

/** Symbol je Referenzstatus: dieselben Symbole wie die Schweregrade der zugehörigen Diagnose. */
export const REFERENCE_SYMBOLS: Readonly<Record<ReferenceStatus, string>> = {
  resolved: OK_SYMBOL,
  unresolved: SEVERITY_SYMBOLS.error,
  ambiguous: SEVERITY_SYMBOLS.warning,
  external_or_unloaded: SEVERITY_SYMBOLS.info,
};

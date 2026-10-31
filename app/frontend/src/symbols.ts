// Symbole der Schweregrade und Status (docs/decisions.md, „Symbol für Warnung“).
// Symbole sind sprachunabhängig; der zugehörige Text steht immer in den Sprachdateien.

import type { Severity } from "./types";

export const SEVERITY_SYMBOLS: Readonly<Record<Severity, string>> = {
  error: "⚠",
  warning: "△",
  info: "ℹ",
};

export const OK_SYMBOL = "✔";

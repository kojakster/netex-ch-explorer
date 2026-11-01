// Logik der Objektliste nach Frames: Zählung, Auf-/Zuklappen und sichtbare Einträge.

import type { ObjectTreeEntry } from "./types";

/** Frames mit mehr Objekten starten zugeklappt (die Liste bleibt kurz und schnell). */
export const COLLAPSE_THRESHOLD = 200;

/** Höchste dargestellte Einrückungsebene; tiefer Verschachteltes bleibt gleich weit eingerückt. */
export const MAX_INDENT_LEVEL = 8;

/** Anzahl der Objekte (ohne Frames) unter dem Frame an Position `index`, verschachtelte Frames eingeschlossen. */
export function objectCountBelow(entries: readonly ObjectTreeEntry[], index: number): number {
  const frame = entries[index];
  if (frame === undefined) {
    return 0;
  }
  let count = 0;
  for (let next = index + 1; next < entries.length; next += 1) {
    const entry = entries[next];
    if (entry === undefined || entry.depth <= frame.depth) {
      break;
    }
    if (!entry.isFrame) {
      count += 1;
    }
  }
  return count;
}

/** Ob ein Frame offen ist: ausdrückliche Wahl des Benutzers, sonst offen bis zur Schwelle. */
export function isFrameOpen(
  choice: boolean | undefined,
  objectCount: number,
  threshold: number = COLLAPSE_THRESHOLD,
): boolean {
  return choice ?? objectCount <= threshold;
}

/** Ein sichtbarer Eintrag mit Zählung (nur bei Frames sinnvoll) und Offen-Zustand. */
export interface VisibleEntry {
  entry: ObjectTreeEntry;
  objectCount: number;
  open: boolean;
}

/**
 * Sichtbare Einträge: Unterhalb eines zugeklappten Frames wird alles ausgeblendet, was tiefer
 * eingerückt ist. `choices` enthält die Wahl des Benutzers je Frame (Objekt-ID).
 */
export function visibleEntries(
  entries: readonly ObjectTreeEntry[],
  choices: ReadonlyMap<string, boolean>,
  threshold: number = COLLAPSE_THRESHOLD,
): VisibleEntry[] {
  const visible: VisibleEntry[] = [];
  let hiddenBelow: number | null = null;
  entries.forEach((entry, index) => {
    if (hiddenBelow !== null) {
      if (entry.depth > hiddenBelow) {
        return;
      }
      hiddenBelow = null;
    }
    const objectCount = entry.isFrame ? objectCountBelow(entries, index) : 0;
    const open = entry.isFrame
      ? isFrameOpen(choices.get(entry.object.id), objectCount, threshold)
      : true;
    visible.push({ entry, objectCount, open });
    if (entry.isFrame && !open) {
      hiddenBelow = entry.depth;
    }
  });
  return visible;
}

// Breite der verstellbaren Spalten: Grenzen, Tastaturschritte und Merken im Browser (localStorage).

import { useCallback, useEffect, useState } from "react";

/** Grenzen und Standardwert einer verstellbaren Spalte (in Pixeln). */
export interface WidthLimits {
  min: number;
  max: number;
  initial: number;
}

/** Schritt der Pfeiltasten und der grosse Schritt (mit Umschalttaste) in Pixeln. */
export const KEY_STEP = 16;
export const KEY_STEP_LARGE = 64;

export const SIDEBAR_LIMITS: WidthLimits = { min: 220, max: 560, initial: 288 };
export const DETAILS_LIMITS: WidthLimits = { min: 320, max: 900, initial: 420 };
/** Mindestbreite des Hauptbereichs; die Spalten daneben geben vorher nach. */
export const MAIN_MIN_WIDTH = 360;
/** Platz neben den Spalten: Seitenrand und je Griff (siehe `.layout` in `styles.css`). */
export const LAYOUT_CHROME_WIDTH = 32;
export const HANDLE_WIDTH = 20;

/** Fensterbreiten der Umbruch-Regeln in `styles.css`: bis 800 px einspaltig, bis 1279 px unten. */
export const SINGLE_COLUMN_MAX_VIEWPORT = 800;
export const WRAPPED_DETAILS_MAX_VIEWPORT = 1279;

export const SIDEBAR_STORAGE_KEY = "netex-ch-explorer.sidebarWidth";
export const DETAILS_STORAGE_KEY = "netex-ch-explorer.detailsWidth";

/** Klemmt `value` auf `min` bis `max` (ist `max` kleiner als `min`, gilt `min`). */
export function clampWidth(value: number, min: number, max: number): number {
  return Math.round(Math.min(Math.max(value, min), Math.max(min, max)));
}

/**
 * Grösste Breite einer Spalte, ohne dass der Hauptbereich unter seine Mindestbreite fällt.
 * `otherWidth` ist die Breite der anderen verstellbaren Spalte (0, wenn sie fehlt).
 */
export function maxWidthFor(
  limits: WidthLimits,
  viewport: number,
  otherWidth: number,
  handles: number,
): number {
  const free =
    viewport - LAYOUT_CHROME_WIDTH - handles * HANDLE_WIDTH - MAIN_MIN_WIDTH - otherWidth;
  return clampWidth(free, limits.min, limits.max);
}

/** Breite und Obergrenze einer Spalte; `handle` sagt, ob ihr Griff bei dieser Fenstergrösse gilt. */
export interface ColumnState {
  width: number;
  max: number;
  handle: boolean;
}

/**
 * Wirksame Breiten beider Spalten für die Fensterbreite. Die Navigation wird zuerst bemessen
 * (die rechte Spalte behält mindestens ihre Mindestbreite), die rechte Spalte erhält den Rest;
 * der Hauptbereich behält seine Mindestbreite. Bei schmalem Fenster entfallen die Griffe.
 */
export function columnLayout(
  viewport: number,
  hasSidebar: boolean,
  hasDetails: boolean,
  storedSidebar: number,
  storedDetails: number,
): { sidebar: ColumnState; details: ColumnState } {
  const sidebarBeside = hasSidebar && viewport > SINGLE_COLUMN_MAX_VIEWPORT;
  const detailsBeside = hasDetails && viewport > WRAPPED_DETAILS_MAX_VIEWPORT;
  const handles = (sidebarBeside ? 1 : 0) + (detailsBeside ? 1 : 0);
  const sidebarMax = maxWidthFor(
    SIDEBAR_LIMITS,
    viewport,
    detailsBeside ? DETAILS_LIMITS.min : 0,
    handles,
  );
  const sidebarWidth = clampWidth(storedSidebar, SIDEBAR_LIMITS.min, sidebarMax);
  const detailsMax = maxWidthFor(
    DETAILS_LIMITS,
    viewport,
    sidebarBeside ? sidebarWidth : 0,
    handles,
  );
  return {
    sidebar: { width: sidebarWidth, max: sidebarMax, handle: sidebarBeside },
    details: {
      width: clampWidth(storedDetails, DETAILS_LIMITS.min, detailsMax),
      max: detailsMax,
      handle: detailsBeside,
    },
  };
}

/** Neue Breite nach einer Taste; `null`, wenn die Taste nichts verändert. */
export function widthAfterKey(
  key: string,
  shift: boolean,
  width: number,
  min: number,
  max: number,
  growsToRight: boolean,
): number | null {
  const step = shift ? KEY_STEP_LARGE : KEY_STEP;
  const direction = growsToRight ? 1 : -1;
  switch (key) {
    case "ArrowRight":
      return clampWidth(width + direction * step, min, max);
    case "ArrowLeft":
      return clampWidth(width - direction * step, min, max);
    case "Home":
      return min;
    case "End":
      return max;
    default:
      return null;
  }
}

/** Gespeicherte Breite als Zahl; `null` bei fehlendem oder ungültigem Wert. */
export function parseStoredWidth(raw: string | null): number | null {
  if (raw === null || !/^\d{1,5}$/.test(raw)) {
    return null;
  }
  return Number(raw);
}

function readStored(key: string): number | null {
  try {
    return parseStoredWidth(window.localStorage.getItem(key));
  } catch {
    return null;
  }
}

function writeStored(key: string, width: number | null): void {
  try {
    if (width === null) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, String(width));
    }
  } catch {
    // Speicher gesperrt oder voll: die Breite gilt dann nur für diese Sitzung.
  }
}

/** Gemerkte Breite einer Spalte: Wert, Setzen (merkt ihn) und Zurücksetzen auf den Standard. */
export function useStoredWidth(
  storageKey: string,
  limits: WidthLimits,
): [number, (width: number) => void, () => void] {
  const [width, setWidth] = useState(() =>
    clampWidth(readStored(storageKey) ?? limits.initial, limits.min, limits.max),
  );
  const set = useCallback(
    (next: number) => {
      const clamped = clampWidth(next, limits.min, limits.max);
      setWidth(clamped);
      writeStored(storageKey, clamped);
    },
    [storageKey, limits.min, limits.max],
  );
  const reset = useCallback(() => {
    setWidth(limits.initial);
    writeStored(storageKey, null);
  }, [storageKey, limits.initial]);
  return [width, set, reset];
}

/** Breite des Fensters; ändert sich beim Verkleinern oder Vergrössern. */
export function useViewportWidth(): number {
  const [viewport, setViewport] = useState(() => window.innerWidth);
  useEffect(() => {
    const update = () => setViewport(window.innerWidth);
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);
  return viewport;
}

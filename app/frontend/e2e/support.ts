// Gemeinsame Hilfen des E2E-Tests: Pfade und Konfiguration des Projekts (keine festen Pfade).

import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

export const PROJECT_ROOT = resolve(import.meta.dirname, "..", "..", "..");
export const REQUIRE_GUIDE_ENV = "NETEX_REQUIRE_GUIDE";

function readJson(relativePath: string): unknown {
  return JSON.parse(readFileSync(join(PROJECT_ROOT, relativePath), "utf-8"));
}

/** Pfad des Guide-Klons laut config/settings.json (relativ zum Projektordner). */
export function guidePath(): string {
  const settings = readJson("config/settings.json") as { guidePath: string };
  return resolve(PROJECT_ROOT, settings.guidePath);
}

export function guideAvailable(): boolean {
  return existsSync(join(guidePath(), ".git"));
}

/** Hintergrundfarbe eines Frames laut config/frame-colors.json (`#RRGGBB`). */
export function frameBackground(frame: string): string {
  const colors = readJson("config/frame-colors.json") as Record<
    string,
    { background: string } | undefined
  >;
  const entry = colors[frame];
  if (entry === undefined) {
    throw new Error(`Frame ohne Farbe in config/frame-colors.json: ${frame}`);
  }
  return entry.background;
}

/** `#RRGGBB` als `rgb(r, g, b)`, wie der Browser berechnete Farben liefert. */
export function toRgb(hex: string): string {
  const [red, green, blue] = [1, 3, 5].map((start) =>
    Number.parseInt(hex.slice(start, start + 2), 16),
  );
  return `rgb(${red}, ${green}, ${blue})`;
}

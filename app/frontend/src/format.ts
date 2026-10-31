// Darstellung von Zeiten und Daten (Werte aus der Datei, ohne Übersetzung).

/** `10:35:00` wird `10:35`; Sekunden bleiben stehen, wenn sie nicht 0 sind. */
export function trimSeconds(clock: string): string {
  return clock.endsWith(":00") ? clock.slice(0, 5) : clock;
}

/** Verschiebung zum Betriebstag: `+1`, `−1`; bei 0 leer. */
export function dayMarker(dayOffset: number): string {
  if (dayOffset === 0) {
    return "";
  }
  return dayOffset > 0 ? `+${dayOffset}` : `−${Math.abs(dayOffset)}`;
}

/** Zeit mit Tagesmarke, z. B. `00:17 +1`. */
export function timeWithDay(clock: string, dayOffset: number): string {
  const marker = dayMarker(dayOffset);
  return marker === "" ? trimSeconds(clock) : `${trimSeconds(clock)} ${marker}`;
}

/** ISO-Datum (`2026-12-14`) als `14.12.2026` für Deutsch, sonst unverändert. */
export function formatDate(iso: string, language: string): string {
  const match = /^(\d{4,})-(\d{2})-(\d{2})$/.exec(iso);
  if (match === null || !language.startsWith("de")) {
    return iso;
  }
  return `${match[3]}.${match[2]}.${match[1]}`;
}

/** Erste sieben Zeichen eines Commits. */
export function shortCommit(commit: string | null): string {
  return commit === null ? "" : commit.slice(0, 7);
}

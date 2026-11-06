// Anzeige des Commit-Datums: Datum und Uhrzeit so, wie sie im Commit stehen (Zeitzone des Committers).

const ISO_DATE_TIME = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/;

/** `2026-11-04T09:16:10+01:00` → `04.11.2026 09:16` (de) bzw. `2026-11-04 09:16` (sonst). */
export function formatCommitDate(iso: string, language: string): string | null {
  const match = ISO_DATE_TIME.exec(iso);
  if (match === null) {
    return null;
  }
  const [, year, month, day, hours, minutes] = match;
  const date = language.startsWith("de") ? `${day}.${month}.${year}` : `${year}-${month}-${day}`;
  return `${date} ${hours}:${minutes}`;
}

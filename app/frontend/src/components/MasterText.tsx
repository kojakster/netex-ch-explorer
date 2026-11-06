import { shortCommit } from "../format";
import { useI18n } from "../i18n";
import type { MasterInfo, MasterMatchInfo } from "../types";

/** Blatt „Angebote“: Spalten für die Kurzform „Text (Abkürzung)“. */
const OFFER_SHEET = "Angebote";
const OFFER_CODE_LABEL = "Angebotabkürzung";
const OFFER_TEXT_LABEL = "Angebottext";

/** Kurzfassung einer Zeile: „Bistro (WS)“ bei Angeboten, sonst die ersten zwei Werte. */
export function masterSummary(match: MasterMatchInfo): string {
  if (match.sheet === OFFER_SHEET) {
    const code = match.texts.find((text) => text.label === OFFER_CODE_LABEL)?.text;
    const name = match.texts.find((text) => text.label === OFFER_TEXT_LABEL)?.text;
    if (code !== undefined && name !== undefined) {
      return `${name} (${code})`;
    }
  }
  return match.texts
    .slice(0, 2)
    .map((text) => text.text)
    .join(" \u00b7 ");
}

/** Excel-Symbol: kennzeichnet Werte, die aus der Mappingtabelle (Excel) stammen. */
export function ExcelIcon({ title }: { title: string }) {
  return (
    <svg
      className="excel-icon"
      viewBox="0 0 16 16"
      width="14"
      height="14"
      role="img"
      aria-label={title}
    >
      <title>{title}</title>
      <rect x="1" y="1" width="14" height="14" rx="2" fill="#1D6F42" />
      <path d="M4.5 4.5l7 7M11.5 4.5l-7 7" stroke="#FFFFFF" strokeWidth="1.8" fill="none" />
    </svg>
  );
}

interface MasterTextProps {
  master: MasterInfo | null;
  guideCommit: string | null;
  /** Kurzfassung für Tabellenzellen: nur die ersten zwei Werte je Zeile. */
  compact?: boolean;
}

/** Bedeutung eines Codes aus den Stammdaten, mit Blatt, Zeile und Guide-Stand. */
export function MasterText({ master, guideCommit, compact = false }: MasterTextProps) {
  const { t } = useI18n();
  if (master === null) {
    return null;
  }
  if (master.status === "unavailable") {
    return <span className="master master-none">{t("master.unavailable")}</span>;
  }
  if (master.status === "none") {
    return <span className="master master-none">{t("master.none")}</span>;
  }
  return (
    <span className="master">
      {master.matches.map((match) => {
        const source = t("master.source", {
          sheet: match.sheet,
          row: match.row,
          commit: shortCommit(guideCommit),
        });
        const summary = masterSummary(match);
        if (compact) {
          return (
            <span key={`${match.sheet}|${match.row}`} className="master-match" title={source}>
              <ExcelIcon title={source} /> {summary}
            </span>
          );
        }
        return (
          <details key={`${match.sheet}|${match.row}`} className="master-match master-details">
            <summary>
              <ExcelIcon title={source} /> {summary}
            </summary>
            {match.texts.map((text) => (
              <span key={text.label} className="master-text">
                <span className="master-label">{text.label}</span> {text.text}
              </span>
            ))}
            <span className="master-source">{source}</span>
          </details>
        );
      })}
    </span>
  );
}
